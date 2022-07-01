#include <Arduino.h>
#include <SPI.h>

#define HSPI_MISO 19
#define HSPI_MOSI 23
#define HSPI_SCLK 18
#define HSPI_CS   5
#define SPI_FREQUENCY 10000

static const int spiClk = 240000000; // 1 MHz
SPIClass * hspi = NULL;

uint16_t PARITY = 0x8000;

uint16_t READ_CMD = 0x4000;
uint16_t WRITE_CMD = 0x0000;
uint16_t NOP_CMD = 0x0000;
uint16_t CLEAR_ERROR_CMD = 0x4001;


uint16_t ERROR_ADDR = 0x0001;
uint16_t DIAG_ADDR = 0x3FFD;
uint16_t MAGNITUDE_ADDR = 0x3FFE;
uint16_t ANGLE_ADDR = 0x3FFF;


void setup() {
    Serial.begin(115200);
    //hspi = new SPIClass(HSPI);
    //hspi->begin();
    SPI.begin(HSPI_SCLK, HSPI_MISO, HSPI_MOSI, HSPI_CS); //SCLK, MISO, MOSI, SS
    //SPI.setFrequency(1000);
    pinMode(HSPI_CS, OUTPUT); //HSPI SS
    //SPI.setHwCs(true);
    digitalWrite(HSPI_CS, HIGH);
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

void printPayload(uint16_t payload) {
    bool parityCheck = !calcEvenParity(payload);
    bool parityBit = (0x8000 & payload) >> 15;
    bool efrBit = (0x4000 & payload) >> 14;
    uint16_t data = 0x3FFF & payload;

    Serial.printf("payload: 0x%04x ; parity: %d ; efr: %d ; data: %d ; parityCheck: %d\n", payload, parityBit, efrBit, data, parityCheck);
}

void printResult(uint16_t payload) {
    bool parityCheck = !calcEvenParity(payload);
    bool efrBit = (0x4000 & payload) >> 14;
    uint16_t data = 0x3FFF & payload;

    if (parityCheck && !efrBit) {
        // If no error
        Serial.printf("data: %d\n", data);
    }
    
}

uint16_t transfer(uint16_t payload) {
    payload = paritize(payload);

    SPI.beginTransaction(SPISettings(SPI_FREQUENCY, MSBFIRST, SPI_MODE1));
    digitalWrite(HSPI_CS, LOW);
    uint16_t result1 = SPI.transfer16(payload);
    digitalWrite(HSPI_CS, HIGH);
    SPI.endTransaction();

    return result1;
}

uint16_t transferDebug(uint16_t payload) {
    payload = paritize(payload);
    Serial.printf("DEBUG Command: 0x%04x\n", payload);

    SPI.beginTransaction(SPISettings(SPI_FREQUENCY, MSBFIRST, SPI_MODE1));
    digitalWrite(HSPI_CS, LOW);
    uint16_t result1 = SPI.transfer16(payload);
    digitalWrite(HSPI_CS, HIGH);
    SPI.endTransaction();

    delay(1);

    SPI.beginTransaction(SPISettings(SPI_FREQUENCY, MSBFIRST, SPI_MODE1));
    digitalWrite(HSPI_CS, LOW);
    uint16_t result2 = SPI.transfer16(NOP_CMD);
    digitalWrite(HSPI_CS, HIGH);
    SPI.endTransaction();

    Serial.printf("DEBUG Result1: 0x%04x ; Result2: 0x%04x\n", result1, result2);
    printPayload(result1);
    printPayload(result2);
    return result2;
}

void tests() {
    uint16_t result;
    Serial.println("");

    uint16_t readDiag = READ_CMD | DIAG_ADDR;
    uint16_t readError = READ_CMD | ERROR_ADDR;
    uint16_t readAngle = READ_CMD | ANGLE_ADDR;
    //buff = 0xFFFF;
    //buff = 0b0101010101010101;
    //buff = 0;
    //Serial.printf("Command: 0x%04x\n", buff);

    result = transfer(NOP_CMD);
    delay(100);
    
/*
    result = transfer(NOP_CMD);
    delay(100);

    result = transfer(NOP_CMD);
    delay(100);

    result = transfer(NOP_CMD);
    delay(100);

    result = transfer(readError);
    delay(100);

    result = transfer(readDiag);
    delay(100);

    result = transfer(NOP_CMD);
    delay(100);

    result = transfer(readDiag);
    delay(100);

    result = transfer(readAngle);
    delay(100);
*/
    /*
    result = transfer(readAngle);
    */

    /*
    SPI.beginTransaction(SPISettings(10000, MSBFIRST, SPI_MODE2));
    SPI.transfer16(CLEAR_ERROR_OP);
    uint16_t result = SPI.transfer16(buff);
    Serial.printf("Result1: 0x%04x\n", result);
    result = SPI.transfer16(buff);
    Serial.printf("Result2: 0x%04x\n", result);
    result = SPI.transfer16(buff);
    Serial.printf("Result3: 0x%04x\n", result);
    SPI.endTransaction();
    */

/*
    buff = READ_OP | NOP_ADDR | PARITY;
    Serial.printf("Command: 0x%04x\n", buff);
    SPI.beginTransaction(SPISettings(100000, MSBFIRST, SPI_MODE1));
    result = SPI.transfer16(buff);
    SPI.endTransaction();
    Serial.printf("Result: 0x%04x\n", result);
*/
    //Serial.printf("Buffer: %04u\n", buff);
}

void loop() {
    uint16_t result;

    result = transferDebug(NOP_CMD);
    printResult(result);
    delay(1000);
}
