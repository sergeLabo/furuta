#ifndef lib_model_h
#define lib_model_h

#include <Arduino.h>

struct AngleSensor {
    const uint8_t pinA;
    const uint8_t pinB;
    const uint8_t pinIndex;
    const uint16_t maxPosition;
    int32_t counter;
    uint16_t position;
    const char* name;
};

struct AngleSensorSimulator {
  const uint8_t pinA;
  const uint8_t pinB;
  const uint8_t pinIndex;
  const uint16_t maxPosition;
  int32_t counter;
  int32_t position;
  bool enabled;
  const char* name;
};

#endif
