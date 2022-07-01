#ifndef lib_datagram_h
#define lib_datagram_h

#include <Arduino.h>

#include "rotary_encoder_config.h"
#include "lib_utils.h"
#include "lib_crc.h"

#include "lib_rotary_encoder_controller_2.h"

static const size_t COMMAND_PAYLOAD_SIZE = 4;
static const size_t DATA_PAYLOAD_SIZE = 48; 

void crcCommandPayload(uint8_t* buffer) {
    libcrc::markCrc16(buffer, COMMAND_PAYLOAD_SIZE);
}

void crcDataPayload(uint8_t* buffer, size_t payloadLength) {
    libcrc::markCrc16(buffer, payloadLength);
}

bool isCommandPayloadCrcValid(uint8_t* buffer) {
    return libcrc::checkCrc16(buffer, COMMAND_PAYLOAD_SIZE);
}

bool isDataPayloadCrcValid(uint8_t* buffer) {
    return libcrc::checkCrc16(buffer, DATA_PAYLOAD_SIZE);
}

void printFullPayload(uint8_t* buffer, size_t size) {
    #ifdef LOG_INFO
    Serial.printf("Full payload: [%02x", buffer[0]);
    for (int k = 1; k < size; k++) {
        Serial.printf(" %02x", buffer[k]);
    }
     Serial.println("]");
     #endif
}

void printCommandPayload(uint8_t* buffer) {
    #ifdef LOG_INFO
    Serial.printf("Decoded command payload: ");
    uint16_t crc16 = buffer[0] << 8;
    crc16 += buffer[1];
    uint8_t marker = buffer[2];
    uint8_t command = buffer[3];

    Serial.printf("CRC16: %d ; Marker: %d ; Command: %d\n", crc16, marker, command);
    #endif
}

void buildCommandPayload(uint8_t* buffer, uint8_t marker, uint8_t command) {
    buffer[2] = marker; // marker
    buffer[3] = command; // command
    crcCommandPayload(buffer);
    //printCommandPayload(buffer);
}

uint16_t getCrc16(uint8_t* payload) {
    uint16_t crc = (uint16_t) payload[0];
    crc = crc << 8;
    crc += (uint16_t) payload[1];
    return crc;
}

uint8_t getMarker(uint8_t* payload) {
    return payload[2];
}

uint8_t getCommand(uint8_t* payload) {
    return payload[3];
}

uint16_t getPosition1(uint8_t* payload) {
    uint16_t position1 = (((uint16_t)payload[4]) << 8) + payload[5];
    return position1;
}

uint16_t getPosition2(uint8_t* payload) {
    uint8_t offset = 2+ 2 * SPEEDS_COUNT_TO_KEEP;
    uint16_t position2 = (((uint16_t)payload[4 + offset]) << 8) + payload[5 + offset];
    return position2;
}

void buildRedundantCommandPayload(uint8_t* buffer, uint8_t marker, uint8_t command, uint8_t redundancy) {
    // Write multiple Commande packets in the payload
    for (uint8_t k = 0; k < redundancy; k++) {
        buildCommandPayload(&buffer[k * COMMAND_PAYLOAD_SIZE], marker, command);
    }
}

int cmpfunc(const void* a, const void* b) {
    return (*(int*)a - *(int*)b);
}

uint8_t* getRedundantCommandPayload(uint8_t* buffer, uint8_t redundancy) {
    // Find first redundant command payload with a valid CRC.
    for (uint8_t k = 0; k < redundancy; k++) {
        uint8_t* commandBuffer = &buffer[k * COMMAND_PAYLOAD_SIZE];
        //Serial.printf("Check renduant command #%d : ", k);
        
        if (isCommandPayloadCrcValid(commandBuffer)) {
            #ifdef LOG_DEBUG
            Serial.printf("Good CRC8: ");
            printCommandPayload(commandBuffer);
            #endif
            return commandBuffer;
        } else {
            #ifdef LOG_DEBUG
            Serial.printf("Bad CRC8 : ");
            printCommandPayload(commandBuffer);
            #endif
        }
    }
    
    return NULL;
}

uint8_t* commandFounds = (uint8_t*) malloc(sizeof(uint8_t) * 16);
uint8_t getRedundantCommandPayload2(uint8_t* buffer, uint8_t redundancy) {
    uint8_t commandFoundCount = 0;
    libutils::initArray8(commandFounds, redundancy);
    // Get commant byte of first redundant command with a valid CRC.
    for (uint8_t k = 0; k < redundancy; k++) {
        uint8_t* commandBuffer = &buffer[k * COMMAND_PAYLOAD_SIZE];
        //Serial.printf("Check renduant command #%d : ", k);
        
        if (isCommandPayloadCrcValid(commandBuffer)) {
            #ifdef LOG_DEBUG
            Serial.printf("Good CRC8: ");
            printCommandPayload(commandBuffer);
            #endif
            commandFounds[k] = getCommand(commandBuffer);
            commandFoundCount ++;
        } else {
            #ifdef LOG_DEBUG
            Serial.printf("Bad CRC8 : ");
            printCommandPayload(commandBuffer);
            #endif
        }
    }
    
    uint8_t result = 0;
    if (commandFoundCount > 0) {
        qsort(commandFounds, commandFoundCount, sizeof(uint8_t), cmpfunc);
        result = commandFounds[0];
        uint8_t maxCount = 1, currCount = 1;
        for (uint8_t k = 1 ; k < commandFoundCount ; k++) {
            if (commandFounds[k] == commandFounds[k - 1]) {
                currCount ++;
            } else {
                currCount = 1;
            }

            if (currCount > maxCount) {
                maxCount = currCount;
                result = commandFounds[k]; // If multiple command are equifrequent take the last one.
            }
        }
    }

    return result;
}

void printDataPayload(uint8_t* buffer, size_t speedsCount) {
    #ifdef LOG_INFO
    Serial.printf("Decoded data payload: ");
    uint16_t crc16 = (uint16_t) buffer[0];
    crc16 = crc16 << 8;
    crc16 += (uint16_t) buffer[1];
    uint8_t marker = buffer[2];
    uint8_t extraHeader = buffer[3];
    uint16_t position1 = (buffer[4] << 8) + buffer[5];
    uint16_t position2 = (buffer[6] << 8) + buffer[7];

    int16_t speed10 = (buffer[8] << 8) + buffer[9];
    int16_t speed11 = (buffer[10] << 8) + buffer[11];
    int16_t speed12 = (buffer[12] << 8) + buffer[13];
    int16_t speed13 = (buffer[14] << 8) + buffer[15];
    int16_t speed14 = (buffer[16] << 8) + buffer[17];

    size_t offset = 8 + 2 * speedsCount;
    
    int16_t speed20 = (buffer[offset] << 8) + buffer[offset + 1];
    int16_t speed21 = (buffer[offset + 2] << 8) + buffer[offset + 3];
    int16_t speed22 = (buffer[offset + 4] << 8) + buffer[offset + 5];
    int16_t speed23 = (buffer[offset + 6] << 8) + buffer[offset + 7];
    int16_t speed24 = (buffer[offset + 8] << 8) + buffer[offset + 9];

    offset = 8 + 4 * speedsCount;
    uint16_t buildTimeIn10us = (buffer[offset] << 8) + buffer[offset + 1];
    uint32_t buildTimeInUs = ((uint32_t)buildTimeIn10us) * 10;

    Serial.printf("CRC16: %5d ; Marker: %3d ; Header: %2d ; Position1: %4d ; Position2: %4d ; Speeds1: [%d, %d, %d, %d, %d, ...] ; Speeds2: [%d, %d, %d, %d, %d, ...] ; buildTime: %dµs\n", crc16, marker, extraHeader, position1, position2, speed10, speed11, speed12, speed13, speed14, speed20, speed21, speed22, speed23, speed24, buildTimeInUs);
    #endif
}

uint8_t datagramCounter = 0;
size_t buildFullPayload(uint8_t* buffer, uint8_t marker, int64_t now, RotarySensor* sensor1, RotarySensor* sensor2) {
    int64_t startPayloadBuild = esp_timer_get_time();

    // Sensor Datagram :
    // CRC16 on 2 bytes
    // Marker on 1 byte
    // Extra header on 1 byte (Parity, Speed counts, redundancy, ...)
    // sensor1 payload (2 + 2 * speeds count bytes)
    // sensor2 payload (2 + 2 * speeds count bytes)
    // ...
    // sensorN payload
    // time to build

    size_t p = 0;

    // Room for CRC16
    p += 2;

    // Marker
    buffer[p] = marker;
    p += 1;

    // Extra header
    buffer[p] = datagramCounter & 0x0F; // 4 bits counter
    p += 1;

    // Sensor 1
    p = sensor1->buildPayload(buffer, p, now);

    // Sensor 2
    p = sensor2->buildPayload(buffer, p, now);

    #ifdef LOG_DEBUG
    int64_t endDatagramBuild = esp_timer_get_time();
    #endif

    // CRC16 at first position
    crcDataPayload(buffer, p);

    #ifdef LOG_DEBUG
    int64_t endCrcBuild = esp_timer_get_time();
    #endif

    // Add elapsed time in payload
    int64_t endPayloadBuild = esp_timer_get_time();

    int64_t buildTime64 = (endPayloadBuild - startPayloadBuild) / 10;
    uint16_t shortenTime = libutils::int64toInt16(buildTime64);
    buffer[p] = shortenTime >> 8;
    buffer[p+1] = shortenTime;
    p += 2;

    #ifdef LOG_DEBUG
    uint32_t datagramBuildTime = (uint32_t) (endDatagramBuild - startDatagramBuild);
    uint32_t crcBuildTime = (uint32_t) (endCrcBuild - endDatagramBuild);

    Serial.printf("[Timings] datagram: %dµs ; crc: %dµs\n", datagramBuildTime, crcBuildTime);

    printSensors(now);
    printTimings(timingsBuffer1, timings1.size);
    printSpeeds(speedsBuffer1, timings1.size);
    #endif

    datagramCounter ++;

    return p;
}

bool isMarkerValid(uint8_t* buffer, uint8_t expectedMarker) {
    uint8_t receivedMarker = buffer[2];
    bool validMarker = receivedMarker > 0 && receivedMarker == expectedMarker;
    if (!validMarker) {
        #ifdef LOG_WARN
        Serial.printf("MARKER NOT VALID !!! Expected: %d but got: %d \n", expectedMarker, receivedMarker);
        #endif
        return false;
    }
    //Serial.printf("MARKER IS VALID\n");
    return true;
}



#endif
