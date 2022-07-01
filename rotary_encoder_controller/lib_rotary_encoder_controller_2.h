#ifndef lib_rotary_encoder_controller_h
#define lib_rotary_encoder_controller_h

#include <Arduino.h>
#include <inttypes.h>

#include "lib_utils.h"
#include "lib_circular_buffer.h"
#include "lib_model.h"
// #include "lib_datagram.h"

namespace rotaryEncoderController {

    // FIXME: move mux into RotarySensor object
    portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

    const static int8_t QUADRATURE_STATES[4] = {0, 1, 3, 2};

    /*
        Rotary encoder signals schema.

                +---------+         +---------+            1
                |         |         |         |
            B   |         |         |         |
                |         |         |         |
            ----+         +---------+         +---------+  0
                    +---------+         +---------+      1
                    |         |         |         |
            A         |         |         |         |
                    |         |         |         |
            +---------+         +---------+         +----- 0
    */

    void IRAM_ATTR registerEvent(volatile AngleSensor* sensor, bool eventA) {
        int64_t usTiming = esp_timer_get_time();

        bool aLevel = gpio_get_level((gpio_num_t) sensor->pinA);
        bool bLevel = gpio_get_level((gpio_num_t) sensor->pinB);

        portENTER_CRITICAL(&mux);
        sensor->eventCount ++;

        if ((eventA && aLevel == bLevel) || (!eventA && aLevel != bLevel)) {
            // Increment counter
            circularBuffer::push(sensor->timings, usTiming);
            sensor->counter ++;
        } else {
            // Decrement counter
            circularBuffer::push(sensor->timings, -usTiming);
            sensor->counter --;
        }
        
        if (sensor->quadratureMode) {
            sensor->position = libutils::absMod16(sensor->counter, sensor->maxPosition);
        } else {
            sensor->position = libutils::absMod16(sensor->counter, sensor->maxPosition * 4) / 4;
        }
        portEXIT_CRITICAL(&mux);
    }

    int8_t IRAM_ATTR getState(bool aLevel, bool bLevel) {
        int8_t sensorLevels = aLevel << 1 | bLevel;
        return QUADRATURE_STATES[sensorLevels];
    }

    uint8_t IRAM_ATTR isCwDirection(bool aLevel, bool bLevel, bool eventA) {
        // Return true if turning Clock wise
        return (eventA && aLevel == bLevel) || (!eventA && aLevel != bLevel);
    }

    void IRAM_ATTR registerSmartEvent(volatile AngleSensor* sensor, bool eventA) {
        // If controller missed events since last registered state, take into account missing steps.
        int64_t usTiming = esp_timer_get_time();

        bool aLevel = gpio_get_level((gpio_num_t) sensor->pinA);
        bool bLevel = gpio_get_level((gpio_num_t) sensor->pinB);

        int8_t newState = getState(aLevel, bLevel);
        bool cwDirection = isCwDirection(aLevel, bLevel, eventA);

        portENTER_CRITICAL(&mux);
        // Calculate increment comparing new state with previous state
        int8_t increment;
        if (sensor->previousState == -1) {
            // Initializing: no previous state yet.
            increment = 1;
        } else if (newState == sensor->previousState) {
            // Missed 3 events
            increment = 4;
        } else if (cwDirection) {
            increment = (int8_t) libutils::absMod8(newState - sensor->previousState, 4);
        } else {
            increment = (int8_t) libutils::absMod8(sensor->previousState - newState, 4);
        }

        // If CCW will decrement counter
        if (!cwDirection) {
            increment *= -1;
        }

        // If missed events use mean time.
        // Negative time for CCW move.
        usTiming /= increment;

        sensor->previousState = newState;
        sensor->eventCount ++;
        circularBuffer::push(sensor->timings, usTiming);
        sensor->counter += increment;
        sensor->position = libutils::absMod16(sensor->counter, sensor->maxPosition);
        if (sensor->quadratureMode) {
            sensor->position = libutils::absMod16(sensor->counter, sensor->maxPosition);
        } else {
            sensor->position = libutils::absMod16(sensor->counter, sensor->maxPosition * 4) / 4;
        }
        portEXIT_CRITICAL(&mux);    
    }

    void IRAM_ATTR indexSensor(volatile AngleSensor* sensor) {
        portENTER_CRITICAL(&mux);
        sensor->counter = 0;
        sensor->position = 0;
        sensor->eventCount = 0;
        portEXIT_CRITICAL(&mux);
    }

}

class RotarySensor {

private:
    volatile CircularBuffer timings;
    uint8_t speedsCount;
    volatile AngleSensor sensor;

    int64_t* timingsBuffer;
    int64_t* speedsBuffer;

    void calculateSpeeds(int64_t now) {
        for (size_t k = speedsCount - 1 ; k > 0 ; k --) {
            // Calculate instantaneous speed between timings
            if (timingsBuffer[k] > 0) {
                speedsBuffer[k] = abs(timingsBuffer[k - 1]) - timingsBuffer[k];
            } else {
                speedsBuffer[k] = - abs(timingsBuffer[k - 1]) - timingsBuffer[k];
            }
        }

        // Last speed is calculated with current time
        if (timingsBuffer[0] >= 0) {
            speedsBuffer[0] = now - timingsBuffer[0];
        } else {
            speedsBuffer[0] = - now - timingsBuffer[0];
        }
    }

public:
    // Constructor
    RotarySensor(uint8_t pinA, uint8_t pinB, uint8_t pinIndex, bool quadratureMode, uint16_t points, uint8_t speedsCount, char* name) :
        timings({}), speedsCount(speedsCount), sensor({name, pinA, pinB, pinIndex, quadratureMode, points, (CircularBuffer*) &timings, 0, 0, 0, -1}) {
            begin();
        }

    void begin() {
        circularBuffer::init((CircularBuffer*) &timings, speedsCount);
        timingsBuffer = (int64_t*) malloc(sizeof(int64_t) * speedsCount);
        speedsBuffer = (int64_t*) malloc(sizeof(int64_t) * speedsCount);

        pinMode(sensor.pinA, INPUT_PULLUP);
        pinMode(sensor.pinB, INPUT_PULLUP);
        pinMode(sensor.pinIndex, INPUT_PULLUP);
    }

    void IRAM_ATTR eventA() {
        rotaryEncoderController::registerSmartEvent(&sensor, true);
    }

    void IRAM_ATTR eventB() {
        rotaryEncoderController::registerSmartEvent(&sensor, false);
    }

    void IRAM_ATTR eventIndex() {
        rotaryEncoderController::indexSensor(&sensor);
    }

    AngleSensor* getSensor() {
        return (AngleSensor*) &sensor;
    }

    /**
     * Build data payload at position p in buffer.
     */
    size_t buildPayload(uint8_t* buffer, size_t p, int64_t now) {
        // Sensor Payload :
        // sensor position on 2 bytes
        // Each speed on 2 bytes

        portENTER_CRITICAL(&rotaryEncoderController::mux);
        uint16_t position = sensor.position;
        circularBuffer::copyDataArray((CircularBuffer*) &timings, timingsBuffer, speedsCount);
        portEXIT_CRITICAL(&rotaryEncoderController::mux);

        #ifdef LOG_DEBUG
        int64_t endTransaction = esp_timer_get_time();
        #endif

        calculateSpeeds(now);

        #ifdef LOG_DEBUG
        int64_t endSpeedsCalculation = esp_timer_get_time();
        #endif

        // Position 1
        buffer[p] = position >> 8;
        buffer[p+1] = position;
        p += 2;
        
        // Speeds
        for (size_t k = 0; k < speedsCount; k++) {
            // Limit speed to int16_t format
            int16_t limitedSpeed = libutils::int64toInt16(speedsBuffer[k]);
            buffer[p] = limitedSpeed >> 8;
            buffer[p+1] = limitedSpeed;
            //Serial.printf("int32: 0x%08X (%d) ; int16: %d ; int16: 0x%02X%02X\n", speeds[k], speeds[k], speed, buffer[p], buffer[p+1]);
            p += 2;
        }


        #ifdef LOG_DEBUG
        uint32_t transactionTime = (uint32_t) (endTransaction - now);
        uint32_t speedsCalculationTime = (uint32_t) (endSpeedsCalculation - endTransaction);
        Serial.printf("[Timings] transaction: %dµs ; speeds calc: %dµs\n", transactionTime, speedsCalculationTime);

        //printSensors(now);
        printTimings(timingsBuffer, timings1.size);
        printSpeeds(speedsBuffer, timings1.size);
        #endif
        
        return p;
    }

};

#endif
