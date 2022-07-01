#ifndef lib_rotary_encoder_controller_spi_master_h
#define lib_rotary_encoder_controller_spi_master_h

#include <Arduino.h>
#include <SPI.h>

#include <lib_utils.h>
#include <lib_datagram.h>

static constexpr uint8_t VSPI_SS {5};  // default: GPIO 5
SPIClass master(VSPI);

static const uint32_t BUFFER_SIZE {SPI_WORD_SIZE};
uint8_t spi_master_tx_buf[BUFFER_SIZE];
uint8_t spi_master_rx_buf[BUFFER_SIZE];

void set_buffer(uint8_t* buff, const size_t size) {
    memset(buff, 0, size);
}

void spiMasterSetup() {
    set_buffer(spi_master_tx_buf, BUFFER_SIZE);
    set_buffer(spi_master_rx_buf, BUFFER_SIZE);

    // SPI Master
    // VSPI = CS: 5, CLK: 18, MOSI: 23, MISO: 19
    pinMode(VSPI_SS, OUTPUT);
    pinMode(SPI_CLK, OUTPUT);
    digitalWrite(VSPI_SS, HIGH);
    master.begin(SPI_CLK, SPI_MISO, SPI_MOSI, SPI_CS);
}

void sendSpiTransaction(uint8_t* txBuffer, uint8_t* rxBuffer, size_t length) {
    // start master transaction
    master.beginTransaction(SPISettings(SPI_FREQUENCY, MSBFIRST, SPI_MODE2));
    digitalWrite(VSPI_SS, LOW);
    master.transferBytes(txBuffer, rxBuffer, length);
    digitalWrite(VSPI_SS, HIGH);
    master.endTransaction();
}

const size_t commandLength = 5;
uint8_t timingMarker = 0;

bool sendSpiTimingCommand() {
    timingMarker ++;
    if (timingMarker == 0) {
        // Marker should not equal 0.
        timingMarker ++;
    }

    buildRedundantCommandPayload(spi_master_tx_buf, timingMarker, COMMAND_TIMING, SPI_COMMAND_REDUNDANCY);
    //printFullPayload(spi_master_tx_buf, BUFFER_SIZE);
    
    // MBD: Transfer 1 extra byte because it seems the last byte is not trasnfered !!!
    sendSpiTransaction(spi_master_tx_buf, spi_master_rx_buf, commandLength * SPI_COMMAND_REDUNDANCY + 1);

    return false;
}

bool sendSpiReadCommand() {
    buildRedundantCommandPayload(spi_master_tx_buf, timingMarker, COMMAND_READ, SPI_COMMAND_REDUNDANCY);
    //printFullPayload(spi_master_tx_buf, BUFFER_SIZE);
    
    sendSpiTransaction(spi_master_tx_buf, spi_master_rx_buf, BUFFER_SIZE);
    //printFullPayload(spi_master_rx_buf, BUFFER_SIZE);

    // Check CRC and marker
    return isDataPayloadCrcValid(spi_master_rx_buf) && isMarkerValid(spi_master_rx_buf, timingMarker);
}

bool spiMasterProcess() {
    delayMicroseconds(100);

    sendSpiTimingCommand();

    delayMicroseconds(100);

    int8_t retries = 0;
    int16_t waitTimeUs = 100;
    bool valid = false;
    while(valid = sendSpiReadCommand(), !valid && retries < SPI_READ_MAX_RETRY) {
        delayMicroseconds(waitTimeUs);
        retries ++;
        //waitTime = pow(2, retries);
        #ifdef LOG_DEBUG
        Serial.printf("Retrying sendSpiReadCommand() #%d after %dms... \n", retries, waitTime);
        //printDataPayload(spi_master_rx_buf, SPEEDS_COUNT_TO_KEEP);
        #endif
    };

    return valid;
}

#endif