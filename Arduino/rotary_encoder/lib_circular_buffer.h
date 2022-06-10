#ifndef lib_circular_buffer_h
#define lib_circular_buffer_h

#include <Arduino.h>
#include "lib_utils.h"

struct CircularBuffer {
    size_t size;
    int64_t* data; // circular buffer
    int8_t offset;
    int8_t lastPosition;
};

size_t sizeCircularBuffer(CircularBuffer b) {
    return b.size;
}

void pushCircularBuffer(CircularBuffer *b, int64_t data) {
    b->data[b->offset] = data;
    b->offset ++;
    b->lastPosition ++;

    if (b->offset >= b->size) {
        b->offset = 0;
    }
    if (b->lastPosition >= b->size) {
        b->lastPosition = 0;
    }
}

void resetCircularBuffer(CircularBuffer *b) {
    initArray64(b->data, b->size);
    b->offset = 0;
    b->lastPosition = b->size - 1;
}

void initCircularBuffer(CircularBuffer *cb, size_t size) {
    cb->size = size;
    int64_t* data = (int64_t*) malloc(sizeof(int64_t) * size);
    cb->data = data;
    resetCircularBuffer(cb);
}

int64_t getLastDataCircularBuffer(CircularBuffer cb) {
    return cb.data[cb.lastPosition];
}

void getDataArrayCircularBuffer(CircularBuffer cb, int64_t* buffer, size_t size) {
    // Copy data array in new buffer: first item is last pushed
    for (size_t k = 0; k < size; k ++) {
        int16_t index = cb.lastPosition - k;
        if (index < 0) {
            index += cb.size;
        }
        buffer[k] = cb.data[index];
    }
}

int64_t* orderedData = (int64_t*) malloc(sizeof(int64_t) * 128);
int32_t printCircularBuffer(char* buf, CircularBuffer cb, bool newLine = true) {
    int32_t n = sprintf(buf, "CircularBuffer: ");
    getDataArrayCircularBuffer(cb, orderedData, cb.size);
    n += printArray64as32(buf, orderedData, cb.size);
    if (newLine) {
        n += sprintf(buf, "\n");
    }
    return n;
}

#endif
