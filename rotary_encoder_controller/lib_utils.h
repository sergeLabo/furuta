#ifndef lib_utils_h
#define lib_utils_h

#include <Arduino.h>

namespace libutils {

    uint8_t IRAM_ATTR absMod8(int32_t a, uint8_t b) {
        int32_t c = a % b;
        c = (c < 0) ? c + b : c;
        return (uint8_t) c;
    }

    uint16_t IRAM_ATTR absMod16(int32_t a, uint16_t b) {
        int32_t c = a % b;
        c = (c < 0) ? c + b : c;
        return (uint16_t) c;
    }

    void initArray8(uint8_t* a, size_t size) {
        memset(a, 0, size);
    }

    void initArray32(int32_t* a, size_t size) {
        memset(a, 0, size);
    }

    void initArray64(int64_t* a, size_t size) {
        for (size_t k = 0; k < size; k++) {
            a[k] = 0ULL;
        }
    }

    // Convert int64 to int32 without overflowing.
    int32_t int64toInt32(int64_t i) {
        int32_t val;
        if (i > ((int64_t)INT32_MAX)) {
            val = INT32_MAX;
        } else if (i < ((int64_t)INT32_MIN)) {
            val = INT32_MIN;
        } else {
            val = (int32_t) i;
        }
        return val;
    }

    // Convert int64 to int16 without overflowing.
    int16_t int64toInt16(int64_t i) {
        int16_t val;
        if (i > ((int64_t)INT16_MAX)) {
            val = INT16_MAX;
        } else if (i < ((int64_t)INT16_MIN)) {
            val = INT16_MIN;
        } else {
            val = (int16_t) i;
        }
        return val;
    } 


    int32_t printArray64as32(char* buf, int64_t* a, size_t size) {
        int32_t n = sprintf(buf, "[%d", int64toInt32(a[0]));
        for (size_t k = 1; k < size; k ++) {
            n += sprintf(&(buf[n]), "; %d", int64toInt32(a[k]));
        }
        n += sprintf(&(buf[n]), "]");
        return n;
    }

    bool blinker = false;
    void blinkLed() {
        // Blink led
        blinker = !blinker;
        digitalWrite(LED_PIN, blinker);
    }

}
#endif