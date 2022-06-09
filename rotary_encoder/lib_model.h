#ifndef lib_model_h
#define lib_model_h

#include <Arduino.h>

struct AngleSensor {
    const uint8_t pinA;
    const uint8_t pinB;
    const uint8_t pinIndex;
    const uint16_t maxPosition;
    int32_t position;
    const char* name;
};

struct AngleSensorSimulator {
  const uint8_t pinA;
  const uint8_t pinB;
  const uint8_t pinIndex;
  int32_t position;
  int32_t counter;
  bool enabled;
  const char* name;
};

#endif