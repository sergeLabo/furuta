#ifndef lib_comm_h
#define lib_comm_h

#include <Arduino.h>

namespace libcomm {
        
    bool calcEvenParity(uint16_t payload) {
        //Serial.printf("payload: 0x%04x ; ", payload);

        // Exclude parity bit (Most Significatif Bit)
        byte bitCount = sizeof(payload) * 8;
        byte cnt = 0;
        byte i;

        for (i = 0; i < bitCount; i++) {
            if (payload & 0x1) {
                cnt ++;
            }
            payload >>= 1;
        }

        // Return 1 if odd number of 1 in payload
        bool result = cnt & 0x1;
        //Serial.printf("bitCount: %d ; parity: %d\n", bitCount, result);
        return result;
    }

    uint16_t paritize(uint16_t payload) {
        bool parity = calcEvenParity(payload);
        return payload | (parity << 15);
    }
}

#endif