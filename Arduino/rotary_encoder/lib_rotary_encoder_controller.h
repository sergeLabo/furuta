#ifndef lib_rotary_encoder_controller_h
#define lib_rotary_encoder_controller_h

#include <Arduino.h>
#include <inttypes.h>

#include "lib_utils.h"
#include "lib_circular_buffer.h"
#include "lib_model.h"
#include "lib_datagram.h"

portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

CircularBuffer timings1;
CircularBuffer timings2;

AngleSensor sensor1 = {SENSOR_1_PIN_A, SENSOR_1_PIN_B, SENSOR_1_PIN_INDEX, 16000, 0, 0, "sensor1"};
AngleSensor sensor2 = {SENSOR_2_PIN_A, SENSOR_2_PIN_B, SENSOR_2_PIN_INDEX, 4000, 0, 0, "sensor2"};

void IRAM_ATTR moveSensor1A() {
    bool aLevel = digitalRead(SENSOR_1_PIN_A);
    bool bLevel = digitalRead(SENSOR_1_PIN_B);

    int64_t usTiming = esp_timer_get_time();

    portENTER_CRITICAL(&mux);
    if (aLevel == bLevel) {
        // Increment counter
        pushCircularBuffer(&timings1, usTiming);
        sensor1.counter ++;
    } else {
        // Decrement counter
        pushCircularBuffer(&timings1, -usTiming);
        sensor1.counter --;
    }
    sensor1.position = absMod16(sensor1.counter, sensor1.maxPosition);
    portEXIT_CRITICAL(&mux);
}

void IRAM_ATTR moveSensor1B() {
    bool aLevel = digitalRead(SENSOR_1_PIN_A);
    bool bLevel = digitalRead(SENSOR_1_PIN_B);

    portENTER_CRITICAL(&mux);
    if (aLevel != bLevel) {
        // Increment counter
        pushCircularBuffer(&timings1, esp_timer_get_time());
        sensor1.counter ++;
    } else {
        // Decrement counter
        pushCircularBuffer(&timings1, -esp_timer_get_time());
        sensor1.counter --;
    }
    sensor1.position = absMod16(sensor1.counter, sensor1.maxPosition);
    portEXIT_CRITICAL(&mux);
}

void IRAM_ATTR resetSensor1() {
    portENTER_CRITICAL(&mux);
    sensor1.counter = 0;
    sensor1.position = 0;
    portEXIT_CRITICAL(&mux);
}

void IRAM_ATTR moveSensor2A() {
    bool aLevel = digitalRead(SENSOR_2_PIN_A);
    bool bLevel = digitalRead(SENSOR_2_PIN_B);

    portENTER_CRITICAL(&mux);
    if (aLevel == bLevel) {
        // Increment position
        pushCircularBuffer(&timings2, esp_timer_get_time());
        sensor2.counter ++;
    } else {
        // Decrement position
        pushCircularBuffer(&timings2, -esp_timer_get_time());
        sensor2.counter --;
    }
    sensor2.position = absMod16(sensor2.counter, sensor2.maxPosition);
    portEXIT_CRITICAL(&mux);
}

void IRAM_ATTR moveSensor2B() {
    bool aLevel = digitalRead(SENSOR_2_PIN_A);
    bool bLevel = digitalRead(SENSOR_2_PIN_B);

    portENTER_CRITICAL(&mux);
    if (aLevel != bLevel) {
        // Increment position
        pushCircularBuffer(&timings2, esp_timer_get_time());
        sensor2.counter ++;
    } else {
        // Decrement position
        pushCircularBuffer(&timings2, -esp_timer_get_time());
        sensor2.counter --;
    }
    sensor2.position = absMod16(sensor2.counter, sensor2.maxPosition);
    portEXIT_CRITICAL(&mux);
}

void IRAM_ATTR resetSensor2() {
    portENTER_CRITICAL(&mux);
    sensor2.counter = 0;
    sensor2.position = 0;
    portEXIT_CRITICAL(&mux);
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
    getDataArrayCircularBuffer(timings1, timingsBuffer1, timings1.size);
    getDataArrayCircularBuffer(timings2, timingsBuffer2, timings2.size);
    calculateSpeeds(timingsBuffer1, speedsBuffer1, timings1.size, now);
    calculateSpeeds(timingsBuffer2, speedsBuffer2, timings2.size, now);

    int32_t n = sprintf(buf, "[%s] position: %d ", sensor1.name, sensor1.position);
    n += speedsMessage(&buf[n], speedsBuffer1, timings1.size);
    n += sprintf(&buf[n], " ; [%s] position: %d ", sensor2.name, sensor2.position);
    n += speedsMessage(&buf[n], speedsBuffer2, timings2.size);
    return n;
}

char* sensorsMessageBuffer = (char*) malloc(sizeof(char) * 256);
void printSensors(int64_t now) {
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
    getDataArrayCircularBuffer(timings1, timingsBuffer1, timings1.size);
    getDataArrayCircularBuffer(timings2, timingsBuffer2, timings2.size);

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
