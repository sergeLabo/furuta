#ifndef lib_rotary_encoder_controller_h
#define lib_rotary_encoder_controller_h

#include <Arduino.h>
#include <inttypes.h>

#include "lib_utils.h"
#include "lib_circular_buffer.h"
#include "lib_model.h"
#include "lib_datagram.h"

portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

const static int8_t QUADRATURE_STATES[4] = {0, 1, 3, 2};

CircularBuffer timings1;
CircularBuffer timings2;

volatile AngleSensor sensor1 = {"sensor1", SENSOR_1_PIN_A, SENSOR_1_PIN_B, SENSOR_1_PIN_INDEX, true, 1000, &timings1, 0, 0, 0, -1};
volatile AngleSensor sensor2 = {"sensor2", SENSOR_2_PIN_A, SENSOR_2_PIN_B, SENSOR_2_PIN_INDEX, true, 1000, &timings2, 0, 0, 0, -1};

/*
    Rotary encoder signals schema.Z

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
        pushCircularBuffer(sensor->timings, usTiming);
        sensor->counter ++;
    } else {
        // Decrement counter
        pushCircularBuffer(sensor->timings, -usTiming);
        sensor->counter --;
    }
    
    if (sensor->quadratureMode) {
        sensor->position = absMod16(sensor->counter, sensor->maxPosition);
    } else {
        sensor->position = absMod16(sensor->counter, sensor->maxPosition * 4) / 4;
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
        increment = (int8_t) absMod8(newState - sensor->previousState, 4);
    } else {
        increment = (int8_t) absMod8(sensor->previousState - newState, 4);
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
    pushCircularBuffer(sensor->timings, usTiming);
    sensor->counter += increment;
    sensor->position = absMod16(sensor->counter, sensor->maxPosition);
    if (sensor->quadratureMode) {
        sensor->position = absMod16(sensor->counter, sensor->maxPosition);
    } else {
        sensor->position = absMod16(sensor->counter, sensor->maxPosition * 4) / 4;
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

void IRAM_ATTR moveSensor1A() {
    registerSmartEvent(&sensor1, true);
}

void IRAM_ATTR moveSensor1B() {
    registerSmartEvent(&sensor1, false);
}

void IRAM_ATTR resetSensor1() {
    indexSensor(&sensor1);
}

void IRAM_ATTR moveSensor2A() {
    registerSmartEvent(&sensor2, true);
}

void IRAM_ATTR moveSensor2B() {
    registerSmartEvent(&sensor2, false);
}

void IRAM_ATTR resetSensor2() {
    indexSensor(&sensor2);
}

int64_t* timingsBuffer1 = (int64_t*) malloc(sizeof(int64_t) * SPEEDS_COUNT_TO_KEEP);
int64_t* timingsBuffer2 = (int64_t*) malloc(sizeof(int64_t) * SPEEDS_COUNT_TO_KEEP);
int64_t* speedsBuffer1 = (int64_t*) malloc(sizeof(int64_t) * SPEEDS_COUNT_TO_KEEP);
int64_t* speedsBuffer2 = (int64_t*) malloc(sizeof(int64_t) * SPEEDS_COUNT_TO_KEEP);

void calculateSpeeds(int64_t* timings, int64_t* speedBuffer, size_t size, int64_t now) {
    for (size_t k = size - 1 ; k > 0 ; k --) {
        // Calculate instantaneous speed between timings
        if (timings[k] > 0) {
            speedBuffer[k] = abs(timings[k - 1]) - timings[k];
        } else {
            speedBuffer[k] = - abs(timings[k - 1]) - timings[k];
        }
    }

    // Last speed is calculated with current time
    if (timings[0] >= 0) {
        speedBuffer[0] = now - timings[0];
    } else {
        speedBuffer[0] = - now - timings[0];
    }
}

int32_t speedsMessage(char* buf, int64_t* speeds, size_t size) {
    int32_t n = sprintf(buf, "speeds: ");
    n += printArray64as32(&buf[n], speeds, size);
    return n;
}

int32_t timingsMessage(char* buf, int64_t* timings, size_t size) {
    int32_t n = sprintf(buf, "timings: ");
    n += printArray64as32(&buf[n], timings, size);
    return n;
}

const char* sensorMessage(AngleSensor* sensor, int64_t* speeds, size_t speedSize) {
    char* buf = (char*) malloc(sizeof(char) * 128);
    int32_t n = sprintf(buf, "[%s] position: %d ", sensor->name, sensor->position);
    n += speedsMessage(&buf[n], speeds, speedSize);
    return buf;
}

int32_t sensorsMessage(char* buf, int64_t now) {
    getDataArrayCircularBuffer(&timings1, timingsBuffer1, timings1.size);
    getDataArrayCircularBuffer(&timings2, timingsBuffer2, timings2.size);
    calculateSpeeds(timingsBuffer1, speedsBuffer1, timings1.size, now);
    calculateSpeeds(timingsBuffer2, speedsBuffer2, timings2.size, now);

    int32_t n = sprintf(buf, "[%s] position1: %d counter1: %d events1: %d ", sensor1.name, sensor1.position, sensor1.counter, sensor1.eventCount);
    n += sprintf(&buf[n], " ; [%s] position2: %d counter2: %d events2: %d ", sensor2.name, sensor2.position, sensor2.counter, sensor2.eventCount);
    n += speedsMessage(&buf[n], speedsBuffer1, timings1.size);
    n += speedsMessage(&buf[n], speedsBuffer2, timings2.size);
    return n;
}

char* sensorsMessageBuffer = (char*) malloc(sizeof(char) * 256);
void printSensors(int64_t now = esp_timer_get_time()) {
    sensorsMessage(sensorsMessageBuffer, now);
    Serial.printf("%s\n", sensorsMessageBuffer);
}

void printSpeeds(int64_t* speeds, size_t size) {
    speedsMessage(sensorsMessageBuffer, speeds, size);
    Serial.printf("%s\n", sensorsMessageBuffer);
}

void printTimings(int64_t* timings, size_t size) {
    timingsMessage(sensorsMessageBuffer, timings, size);
    Serial.printf("%s\n", sensorsMessageBuffer);
}

size_t buildDatagram(uint8_t* buffer, uint8_t marker) {
    int64_t now = esp_timer_get_time();
    
    portENTER_CRITICAL(&mux);
    // Copy timings and position in a transaction

    // Timings
    getDataArrayCircularBuffer(&timings1, timingsBuffer1, timings1.size);
    getDataArrayCircularBuffer(&timings2, timingsBuffer2, timings2.size);

    uint16_t position1 = sensor1.position;
    uint16_t position2 = sensor2.position;

    portEXIT_CRITICAL(&mux);

    #ifdef LOG_DEBUG
    int64_t endTransaction = esp_timer_get_time();
    #endif

    // Speeds
    calculateSpeeds(timingsBuffer1, speedsBuffer1, timings1.size, now);
    calculateSpeeds(timingsBuffer2, speedsBuffer2, timings2.size, now);

    #ifdef LOG_DEBUG
    int64_t endSpeedsCalculation = esp_timer_get_time();
    #endif
    
    size_t p = buildDataPayload(buffer, marker, now, position1, speedsBuffer1, timings1.size, position2, speedsBuffer2, timings2.size);

    #ifdef LOG_DEBUG
    uint32_t transactionTime = (uint32_t) (endTransaction - now);
    uint32_t speedsCalculationTime = (uint32_t) (endSpeedsCalculation - endTransaction);
    Serial.printf("[Timings] transaction: %dµs ; speeds calc: %dµs\n", transactionTime, speedsCalculationTime);

    printSensors(now);
    printTimings(timingsBuffer1, timings1.size);
    printSpeeds(speedsBuffer1, timings1.size);
    #endif

    return p;
}

void printSensorInputs() {
    Serial.printf("INPUTS  [%s] pinA(%d): %d pinB(%d): %d pinIndex(%d): %d", sensor1.name, sensor1.pinA, digitalRead(sensor1.pinA), sensor1.pinB, digitalRead(sensor1.pinB), sensor1.pinIndex, digitalRead(sensor1.pinIndex));
    Serial.printf(" ; [%s] pinA(%d): %d pinB(%d): %d pinIndex(%d): %d\n", sensor2.name, sensor2.pinA, digitalRead(sensor2.pinA), sensor2.pinB, digitalRead(sensor2.pinB), sensor2.pinIndex, digitalRead(sensor2.pinIndex));
}

const char* positionMessage(AngleSensor* sensor) {
    char* buf = (char*) malloc(sizeof(char) * 16);
    sprintf(buf, "%d", sensor->position);
    return buf;
}

void controllerSetup() {
    initCircularBuffer(&timings1, SPEEDS_COUNT_TO_KEEP);
    initCircularBuffer(&timings2, SPEEDS_COUNT_TO_KEEP);

    // Sensor 1
    pinMode(sensor1.pinA, INPUT_PULLUP);
    pinMode(sensor1.pinB, INPUT_PULLUP);
    pinMode(sensor1.pinIndex, INPUT_PULLUP);
    attachInterrupt(sensor1.pinA, moveSensor1A, CHANGE);
    attachInterrupt(sensor1.pinB, moveSensor1B, CHANGE);
    attachInterrupt(sensor1.pinIndex, resetSensor1, RISING);

    // Sensor 2
    pinMode(sensor2.pinA, INPUT_PULLUP);
    pinMode(sensor2.pinB, INPUT_PULLUP);
    pinMode(sensor2.pinIndex, INPUT_PULLUP);
    attachInterrupt(sensor2.pinA, moveSensor2A, CHANGE);
    attachInterrupt(sensor2.pinB, moveSensor2B, CHANGE);
    attachInterrupt(sensor2.pinIndex, resetSensor2, RISING);
}

#endif
