#ifndef lib_model_h
#define lib_model_h

#include <Arduino.h>

#include "lib_circular_buffer.h"

struct AngleSensor {
    const char* name;
    const uint8_t pinA;
    const uint8_t pinB;
    const uint8_t pinIndex;
    const bool quadratureMode; // true if quadrature mode enabled : 4 steps by signal period
    const uint16_t maxPosition; // Position count of sensor
    CircularBuffer* timings;
    // FIXME: actual counter may overflow if always rotating in same direction without reset.
    int32_t counter; // Position not rounded to maxPosition 
    uint16_t position; // Position rounded to maxPosition
    uint32_t eventCount; // Event count received
    int8_t previousState; // One of 4 quadrature state
};

struct AngleSensorSimulator {
  const AngleSensor* sensor;
  const uint8_t pinA;
  const uint8_t pinB;
  const uint8_t pinIndex;
  int32_t counter; // Position not rounded to maxPosition
  uint16_t position; // Position rounded to maxPosition
  uint32_t eventCount; // Event count sent
  int64_t internalState;
  bool enabled;
};

#endif