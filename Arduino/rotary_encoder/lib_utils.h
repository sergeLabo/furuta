#ifndef lib_utils_h
#define lib_utils_h

#include <Arduino.h>

#define CRC16_INITIAL_VALUE   0x0000

int32_t absMod32(int32_t a, uint16_t b) {
    int32_t c = a % b;
    return (c < 0) ? c + b : c;
}

uint16_t absMod16(int32_t a, uint16_t b) {
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

static const uint8_t crc8_table[] = {
    0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15, 0x38, 0x3f, 0x36, 0x31,
    0x24, 0x23, 0x2a, 0x2d, 0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65,
    0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d, 0xe0, 0xe7, 0xee, 0xe9,
    0xfc, 0xfb, 0xf2, 0xf5, 0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd,
    0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85, 0xa8, 0xaf, 0xa6, 0xa1,
    0xb4, 0xb3, 0xba, 0xbd, 0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2,
    0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea, 0xb7, 0xb0, 0xb9, 0xbe,
    0xab, 0xac, 0xa5, 0xa2, 0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a,
    0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32, 0x1f, 0x18, 0x11, 0x16,
    0x03, 0x04, 0x0d, 0x0a, 0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42,
    0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a, 0x89, 0x8e, 0x87, 0x80,
    0x95, 0x92, 0x9b, 0x9c, 0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4,
    0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec, 0xc1, 0xc6, 0xcf, 0xc8,
    0xdd, 0xda, 0xd3, 0xd4, 0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c,
    0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44, 0x19, 0x1e, 0x17, 0x10,
    0x05, 0x02, 0x0b, 0x0c, 0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34,
    0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b, 0x76, 0x71, 0x78, 0x7f,
    0x6a, 0x6d, 0x64, 0x63, 0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b,
    0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13, 0xae, 0xa9, 0xa0, 0xa7,
    0xb2, 0xb5, 0xbc, 0xbb, 0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8d, 0x84, 0x83,
    0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb, 0xe6, 0xe1, 0xe8, 0xef,
    0xfa, 0xfd, 0xf4, 0xf3
};

/*
static const uint8_t crc8_cdma2000_table[] = {
    0x00, 0x9b, 0xad, 0x36, 0xc1, 0x5a, 0x6c, 0xf7, 0x19, 0x82, 0xb4, 0x2f, 
    0xd8, 0x43, 0x75, 0xee, 0x32, 0xa9, 0x9f, 0x04, 0xf3, 0x68, 0x5e, 0xc5, 
    0x2b, 0xb0, 0x86, 0x1d, 0xea, 0x71, 0x47, 0xdc, 0x64, 0xff, 0xc9, 0x52, 
    0xa5, 0x3e, 0x08, 0x93, 0x7d, 0xe6, 0xd0, 0x4b, 0xbc, 0x27, 0x11, 0x8a, 
    0x56, 0xcd, 0xfb, 0x60, 0x97, 0x0c, 0x3a, 0xa1, 0x4f, 0xd4, 0xe2, 0x79, 
    0x8e, 0x15, 0x23, 0xb8, 0xc8, 0x53, 0x65, 0xfe, 0x09, 0x92, 0xa4, 0x3f, 
    0xd1, 0x4a, 0x7c, 0xe7, 0x10, 0x8b, 0xbd, 0x26, 0xfa, 0x61, 0x57, 0xcc, 
    0x3b, 0xa0, 0x96, 0x0d, 0xe3, 0x78, 0x4e, 0xd5, 0x22, 0xb9, 0x8f, 0x14, 
    0xac, 0x37, 0x01, 0x9a, 0x6d, 0xf6, 0xc0, 0x5b, 0xb5, 0x2e, 0x18, 0x83, 
    0x74, 0xef, 0xd9, 0x42, 0x9e, 0x05, 0x33, 0xa8, 0x5f, 0xc4, 0xf2, 0x69, 
    0x87, 0x1c, 0x2a, 0xb1, 0x46, 0xdd, 0xeb, 0x70, 0x0b, 0x90, 0xa6, 0x3d, 
    0xca, 0x51, 0x67, 0xfc, 0x12, 0x89, 0xbf, 0x24, 0xd3, 0x48, 0x7e, 0xe5, 
    0x39, 0xa2, 0x94, 0x0f, 0xf8, 0x63, 0x55, 0xce, 0x20, 0xbb, 0x8d, 0x16, 
    0xe1, 0x7a, 0x4c, 0xd7, 0x6f, 0xf4, 0xc2, 0x59, 0xae, 0x35, 0x03, 0x98, 
    0x76, 0xed, 0xdb, 0x40, 0xb7, 0x2c, 0x1a, 0x81, 0x5d, 0xc6, 0xf0, 0x6b, 
    0x9c, 0x07, 0x31, 0xaa, 0x44, 0xdf, 0xe9, 0x72, 0x85, 0x1e, 0x28, 0xb3, 
    0xc3, 0x58, 0x6e, 0xf5, 0x02, 0x99, 0xaf, 0x34, 0xda, 0x41, 0x77, 0xec, 
    0x1b, 0x80, 0xb6, 0x2d, 0xf1, 0x6a, 0x5c, 0xc7, 0x30, 0xab, 0x9d, 0x06, 
    0xe8, 0x73, 0x45, 0xde, 0x29, 0xb2, 0x84, 0x1f, 0xa7, 0x3c, 0x0a, 0x91, 
    0x66, 0xfd, 0xcb, 0x50, 0xbe, 0x25, 0x13, 0x88, 0x7f, 0xe4, 0xd2, 0x49, 
    0x95, 0x0e, 0x38, 0xa3, 0x54, 0xcf, 0xf9, 0x62, 0x8c, 0x17, 0x21, 0xba, 
    0x4d, 0xd6, 0xe0, 0x7b
};
*/

static uint16_t crc16_table[256] = {
0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7, 
0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef, 
0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6, 
0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de, 
0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485, 
0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d, 
0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4, 
0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc, 
0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823, 
0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b, 
0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12, 
0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a, 
0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41, 
0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49, 
0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70, 
0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78, 
0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f, 
0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067, 
0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e, 
0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256, 
0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d, 
0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405, 
0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c, 
0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634, 
0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab, 
0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3, 
0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a, 
0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92, 
0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9, 
0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1, 
0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8, 
0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
};

/*
static uint16_t crc16_table[256] = {
  0x0000, 0xc0c1, 0xc181, 0x0140, 0xc301, 0x03c0, 0x0280, 0xc241,
  0xc601, 0x06c0, 0x0780, 0xc741, 0x0500, 0xc5c1, 0xc481, 0x0440,
  0xcc01, 0x0cc0, 0x0d80, 0xcd41, 0x0f00, 0xcfc1, 0xce81, 0x0e40,
  0x0a00, 0xcac1, 0xcb81, 0x0b40, 0xc901, 0x09c0, 0x0880, 0xc841,
  0xd801, 0x18c0, 0x1980, 0xd941, 0x1b00, 0xdbc1, 0xda81, 0x1a40,
  0x1e00, 0xdec1, 0xdf81, 0x1f40, 0xdd01, 0x1dc0, 0x1c80, 0xdc41,
  0x1400, 0xd4c1, 0xd581, 0x1540, 0xd701, 0x17c0, 0x1680, 0xd641,
  0xd201, 0x12c0, 0x1380, 0xd341, 0x1100, 0xd1c1, 0xd081, 0x1040,
  0xf001, 0x30c0, 0x3180, 0xf141, 0x3300, 0xf3c1, 0xf281, 0x3240,
  0x3600, 0xf6c1, 0xf781, 0x3740, 0xf501, 0x35c0, 0x3480, 0xf441,
  0x3c00, 0xfcc1, 0xfd81, 0x3d40, 0xff01, 0x3fc0, 0x3e80, 0xfe41,
  0xfa01, 0x3ac0, 0x3b80, 0xfb41, 0x3900, 0xf9c1, 0xf881, 0x3840,
  0x2800, 0xe8c1, 0xe981, 0x2940, 0xeb01, 0x2bc0, 0x2a80, 0xea41,
  0xee01, 0x2ec0, 0x2f80, 0xef41, 0x2d00, 0xedc1, 0xec81, 0x2c40,
  0xe401, 0x24c0, 0x2580, 0xe541, 0x2700, 0xe7c1, 0xe681, 0x2640,
  0x2200, 0xe2c1, 0xe381, 0x2340, 0xe101, 0x21c0, 0x2080, 0xe041,
  0xa001, 0x60c0, 0x6180, 0xa141, 0x6300, 0xa3c1, 0xa281, 0x6240,
  0x6600, 0xa6c1, 0xa781, 0x6740, 0xa501, 0x65c0, 0x6480, 0xa441,
  0x6c00, 0xacc1, 0xad81, 0x6d40, 0xaf01, 0x6fc0, 0x6e80, 0xae41,
  0xaa01, 0x6ac0, 0x6b80, 0xab41, 0x6900, 0xa9c1, 0xa881, 0x6840,
  0x7800, 0xb8c1, 0xb981, 0x7940, 0xbb01, 0x7bc0, 0x7a80, 0xba41,
  0xbe01, 0x7ec0, 0x7f80, 0xbf41, 0x7d00, 0xbdc1, 0xbc81, 0x7c40,
  0xb401, 0x74c0, 0x7580, 0xb541, 0x7700, 0xb7c1, 0xb681, 0x7640,
  0x7200, 0xb2c1, 0xb381, 0x7340, 0xb101, 0x71c0, 0x7080, 0xb041,
  0x5000, 0x90c1, 0x9181, 0x5140, 0x9301, 0x53c0, 0x5280, 0x9241,
  0x9601, 0x56c0, 0x5780, 0x9741, 0x5500, 0x95c1, 0x9481, 0x5440,
  0x9c01, 0x5cc0, 0x5d80, 0x9d41, 0x5f00, 0x9fc1, 0x9e81, 0x5e40,
  0x5a00, 0x9ac1, 0x9b81, 0x5b40, 0x9901, 0x59c0, 0x5880, 0x9841,
  0x8801, 0x48c0, 0x4980, 0x8941, 0x4b00, 0x8bc1, 0x8a81, 0x4a40,
  0x4e00, 0x8ec1, 0x8f81, 0x4f40, 0x8d01, 0x4dc0, 0x4c80, 0x8c41,
  0x4400, 0x84c1, 0x8581, 0x4540, 0x8701, 0x47c0, 0x4680, 0x8641,
  0x8201, 0x42c0, 0x4380, 0x8341, 0x4100, 0x81c1, 0x8081, 0x4040
};
*/

// FIXME: This CRC8 return 0 for a buffer full of 0 so it is valid for an empty transmission which is bad.
uint8_t crc8(uint8_t *p, size_t len) {
    uint16_t i;
    uint16_t crc = 0x0;

    while (len --) {
            i = (crc ^ *p++) & 0xFF;
            crc = (crc8_table[i] ^ (crc << 8)) & 0xFF;
    }

    return crc & 0xFF;
}

uint16_t crc16_old(uint8_t *buf, size_t size) {
    uint16_t crc = CRC16_INITIAL_VALUE;
  const uint8_t *p;

  p = buf;

  while (size--)
    crc = crc16_table[(crc ^ (*p++)) & 0xFF] ^ (crc >> 8);

    return crc;
}

// This uses CRC16-CCITT
// From: http://arduino.cc/forum/index.php/topic,96539.0.html

// This data is from
// http://forum.arduino.cc/index.php?topic=529288.0

// See bottom of this page: http://www.nongnu.org/avr-libc/user-manual/group__util__crc.html
// Polynomial: x^16 + x^12 + x^5 + 1 (0x1021)
uint16_t crc_xmodem_update (uint16_t crc, uint8_t data)
{
  int i;

  crc = crc ^ ((uint16_t)data << 8);
  for (i=0; i<8; i++) {
    if (crc & 0x8000)
      crc = (crc << 1) ^ 0x1021; //(polynomial = 0x1021)
    else
      crc <<= 1;
  }
  return crc;
}

uint16_t crc16(uint8_t *msg, size_t n)
{
  // Initial value. xmodem uses 0xFFFF but this example
  // requires an initial value of zero.
  uint16_t x = 0;

  while(n--) {
    x = crc_xmodem_update(x, (uint16_t)*msg++);
  }
  return(x);
}


void markCrc8(uint8_t *data, size_t length) {
    uint8_t crc = crc8(&data[1], length - 1);
    data[0] = crc;
}

void markCrc16(uint8_t *data, size_t length) {
    uint16_t crc = crc16(&data[2], length - 2);
    data[0] = crc >> 8;
    data[1] = crc;
}

bool checkCrc8(uint8_t *data, size_t length) {
    // CRC8 at first position
    uint8_t received = data[0];
    // Serial.printf("Validating CRC8 with length: %d ...\n", length);
    uint8_t calculated = crc8(&data[1], length - 1);
    if (received != calculated) {
        #ifdef LOG_WARN
        Serial.printf("CRC8 NOT VALID !!! expected: %d but got: %d for length: %d\n", received, calculated, length);
        #endif
        return false;
    }
    //Serial.printf("CRC8 IS VALID\n");
    return true;
}

bool checkCrc16(uint8_t *data, size_t length) {
    // CRC16 at first position
    uint16_t received = (uint16_t) data[0];
    received = received << 8;
    received += (uint16_t) data[1];
    // Serial.printf("Validating CRC16 with length: %d ...\n", length);
    uint16_t calculated = crc16(&data[2], length - 2);
    if (received != calculated) {
        #ifdef LOG_WARN
        Serial.printf("CRC16 NOT VALID !!! expected: %d but got: %d for length: %d\n", received, calculated, length);
        #endif
        return false;
    }
    //Serial.printf("CRC16 IS VALID\n");
    return true;
}

bool blinker = false;
void blinkLed() {
    // Blink led
    blinker = !blinker;
    digitalWrite(LED_PIN, blinker);
}

#endif