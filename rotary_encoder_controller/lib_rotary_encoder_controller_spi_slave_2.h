#ifndef lib_rotary_encoder_controller_spi_slave_h
#define lib_rotary_encoder_controller_spi_slave_h

//#define SOC_SPI_MAXIMUM_BUFFER_SIZE 128
//#define SPI_DMA_DISABLED 1
#include "ESP32SPISlave.h"

#include "lib_rotary_encoder_controller_2.h"
#include "lib_datagram.h"

static constexpr uint8_t VSPI_SS {SS};  // default: GPIO 5
ESP32SPISlave slave;

static const uint32_t BUFFER_SIZE {SPI_WORD_SIZE};
DMA_ATTR uint8_t spi_slave_tx_buf[BUFFER_SIZE];
DMA_ATTR uint8_t spi_slave_rx_buf[BUFFER_SIZE];

DMA_ATTR uint8_t spi_slave_tx_empty[BUFFER_SIZE];
DMA_ATTR uint8_t spi_slave_rx_empty[BUFFER_SIZE];

//uint8_t datagramBuffer[BUFFER_SIZE];

void set_buffer(uint8_t* buff, const size_t size) {
    memset(buff, 0, size);
}

void spiSlaveSetup() {
    set_buffer(spi_slave_tx_buf, BUFFER_SIZE);
    set_buffer(spi_slave_rx_buf, BUFFER_SIZE);

    set_buffer(spi_slave_tx_empty, BUFFER_SIZE);
    set_buffer(spi_slave_rx_empty, BUFFER_SIZE);

    //set_buffer(datagramBuffer, BUFFER_SIZE);

    slave.setDataMode(SPI_MODE0);
    slave.begin(VSPI, SPI_CLK, SPI_MISO, SPI_MOSI, SPI_CS);
    //slave.setQueueSize(1);

    //delay(2000);

    slave.queue(spi_slave_rx_buf, spi_slave_tx_buf, BUFFER_SIZE);
}

void spiSlaveProcess(RotarySensor* sensor1, RotarySensor* sensor2) {
    //Serial.printf("spiSlaveProcess().\n");
    // if transaction has completed from master,
    // available() returns size of results of transaction,
    // and buffer is automatically updated
    while (slave.available()) {
        // do something with `spi_slave_rx_buf`

        //printFullPayload(spi_slave_rx_buf, BUFFER_SIZE);
        //printCommandPayload(spi_slave_rx_buf);

        uint8_t* receivedCommandPayload = getRedundantCommandPayload(spi_slave_rx_buf, SPI_COMMAND_REDUNDANCY);
        if (receivedCommandPayload != NULL) {

            uint8_t receivedCommand = getCommand(receivedCommandPayload);
            //Serial.printf("Received command! %d.\n", receivedCommand);
            if (receivedCommand > 0) {
                //printCommandPayload(spi_slave_rx_buf);

                uint8_t receivedMarker = getMarker(receivedCommandPayload);

                if (receivedCommand == COMMAND_TIMING) {
                    int64_t startTime = esp_timer_get_time();

                    // Master asked for a Timing
                    buildFullPayload(spi_slave_tx_buf, receivedMarker, startTime, sensor1, sensor2);
                } else if (receivedCommand == COMMAND_READ) {
                    // Master asked for a READ
                } else {
                    libutils::blinkLed();
                }

            } else {
                libutils::blinkLed();
            }

        } else {
            // No valid payload found
            #ifdef LOG_WARN
            Serial.printf("No valid payload found !\n");
            #endif
            libutils::blinkLed();
        }

        slave.pop();

        if (slave.remained() == 0) {
            slave.queue(spi_slave_rx_buf, spi_slave_tx_buf, BUFFER_SIZE);
        }

    }
    //TODO: use crc16. Check if delay resolve problem.
}

#endif
