#ifndef lib_rotary_encoder_controller_spi_slave_h
#define lib_rotary_encoder_controller_spi_slave_h

#include "lib_rotary_encoder_controller.h"


//#define SOC_SPI_MAXIMUM_BUFFER_SIZE 128
//#define SPI_DMA_DISABLED 1
#include <ESP32SPISlave.h>

static constexpr uint8_t VSPI_SS {SS};  // default: GPIO 5
ESP32SPISlave slave;

static const uint32_t BUFFER_SIZE {SPI_WORD_SIZE};
uint8_t spi_slave_tx_buf[BUFFER_SIZE];
uint8_t spi_slave_rx_buf[BUFFER_SIZE];

void set_buffer(uint8_t* buff, const size_t size) {
    memset(buff, 0, size);
}

void spiSlaveSetup() {
    set_buffer(spi_slave_tx_buf, SPI_WORD_SIZE);
    set_buffer(spi_slave_rx_buf, SPI_WORD_SIZE);

    slave.setDataMode(SPI_MODE0);
    //slave.begin(VSPI, SPI_CLK, SPI_MISO, SPI_MOSI, SPI_CS);
    slave.begin(HSPI, 11, 9, 10, 8);
    //slave.begin();

    delay(2000);
}

int counter = 0;
void spiSlaveProcess() {
    // if there is no transaction in queue, add transaction
    if (slave.remained() == 0) {

        //sensorsMessage(sensorsMessageBuffer);
        String message = "Hello World " + String(counter, DEC);
        message.concat(" !!!");
        message.toCharArray((char*)spi_slave_tx_buf, SPI_WORD_SIZE);

        Serial.printf("Sending data: ");
        for (int32_t k = 0; k < SPI_WORD_SIZE; k++) {
            Serial.printf("%d ", spi_slave_tx_buf[k]);
        }
        Serial.println();
        //memcpy(&spi_slave_tx_buf, spi_slave_tx_buf, message.length());


        slave.queue(spi_slave_rx_buf, spi_slave_tx_buf, BUFFER_SIZE);

        // Blink led
        counter ++;
        digitalWrite(LED_PIN, counter % 2);
    }

    // if transaction has completed from master,
    // available() returns size of results of transaction,
    // and buffer is automatically updated

    while (slave.available()) {
        slave.pop();


        // show received data
        // for (size_t i = 0; i < BUFFER_SIZE; ++i) {
        //     printf("%d ", spi_slave_rx_buf[i]);
        // }
        // printf("\n");

    }
}

#endif
