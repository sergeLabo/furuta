#ifndef LIB_ROTARY_ENCODER_CONTROLLER_DEBUG_H
#define LIB_ROTARY_ENCODER_CONTROLLER_DEBUG_H

#include <Arduino.h>

#include "lib_utils.h"
#include "lib_model.h"

int32_t speedsMessage(char* buf, int64_t* speeds, size_t size) {
    int32_t n = sprintf(buf, "speeds: ");
    n += libutils::printArray64as32(&buf[n], speeds, size);
    return n;
}

int32_t timingsMessage(char* buf, int64_t* timings, size_t size) {
    int32_t n = sprintf(buf, "timings: ");
    n += libutils::printArray64as32(&buf[n], timings, size);
    return n;
}

const char* sensorMessage(AngleSensor* sensor, int64_t* speeds, size_t speedSize) {
    char* buf = (char*) malloc(sizeof(char) * 128);
    int32_t n = sprintf(buf, "[%s] position: %d ", sensor->name, sensor->position);
    n += speedsMessage(&buf[n], speeds, speedSize);
    return buf;
}

const char* positionMessage(AngleSensor* sensor) {
    char* buf = (char*) malloc(sizeof(char) * 16);
    sprintf(buf, "%d", sensor->position);
    return buf;
}

void printSimulator(AngleSensorSimulator simulator) {
    delay(1);
    Serial.printf("[%s] position: %d\n", simulator.sensor->name, simulator.position);
}

#endif