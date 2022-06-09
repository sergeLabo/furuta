#ifndef lib_circular_buffer_h
#define lib_circular_buffer_h

//#include <Arduino.h>
#include "lib_utils.h"

struct CircularBuffer {
  int32_t data[5]; // circular buffer
  int8_t offset;
  int8_t lastPosition;
  int32_t buffer[5]; // contains ordered data
};

size_t sizeCircularBuffer(CircularBuffer b) {
    size_t size = sizeof(b.data) / sizeof(b.data[0]);
    return size;
}

void pushCircularBuffer(CircularBuffer *b, int32_t data) {
    b->data[b->offset] = data;
    b->offset ++;
    b->lastPosition ++;

    size_t length = sizeof(b->data) / sizeof(b->data[0]);
    if (b->offset >= length) {
        b->offset = 0;
    }
    if (b->lastPosition >= length) {
        b->lastPosition = 0;
    }
}

void resetCircularBuffer(CircularBuffer *b) {
    size_t length = sizeof(b->data) / sizeof(b->data[0]);
    // for (int8_t k = 0 ; k < length; k++) {
    //     pushCircularBuffer(b, 0);
    // }
    initArray(b->data);
    b->offset = 0;
    b->lastPosition = length - 1;
}

int32_t getLastDataCircularBuffer(CircularBuffer b) {
    return b.data[b.lastPosition];
}

int32_t* getDataArrayCircularBuffer(CircularBuffer* b) {
    // Copy data array in new buffer: first item is last pushed
    size_t length = sizeof(b->data) / sizeof(b->data[0]);
    // Serial.printf("length: %d ", length);
    //int32_t* buffer = (int32_t *) malloc(length * sizeof(int32_t));
    int32_t* buffer = b->buffer;
    for (int32_t k = 0; k < 5; k ++) {
        int32_t index = b->lastPosition - k;
        if (index < 0) {
            index += length;
        }
        buffer[k] = b->data[index];
        // buf[k] = k + 1;
    }
    //length = sizeof(buffer) / sizeof(buffer[0]);
    // Serial.printf("length: %d ", length);
    return buffer;
}

int32_t printCircularBuffer(char* buf, CircularBuffer* b, bool newLine = true) {
    int32_t n = sprintf(buf, "CircularBuffer: ");
    int32_t* data = getDataArrayCircularBuffer(b);
    int32_t size = sizeCircularBuffer(*b);
    n += printArray(buf, data, size);
    if (newLine) {
        n += sprintf(buf, "\n");
    }
    return n;
}

#endif
