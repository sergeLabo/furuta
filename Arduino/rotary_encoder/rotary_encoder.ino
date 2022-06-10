#include <Arduino.h>

#define SPI_MISO (gpio_num_t) 19
#define SPI_MOSI (gpio_num_t) 23
#define SPI_CLK (gpio_num_t) 18
#define SPI_CS   (gpio_num_t) 22

#define SENSOR_1_PIN_A (gpio_num_t) 35
#define SENSOR_1_PIN_B (gpio_num_t) 34
#define SENSOR_1_PIN_INDEX (gpio_num_t) 39

#define SENSOR_2_PIN_A (gpio_num_t) 2
#define SENSOR_2_PIN_B (gpio_num_t) 13
#define SENSOR_2_PIN_INDEX (gpio_num_t) 14

#define LED_PIN (gpio_num_t) 5

//#define LOG_WARN

#include "rotary_encoder_config.h"
#include "lib_rotary_encoder_controller.h"
#include "lib_rotary_encoder_controller_spi_slave_2.h"

void setup() {
    Serial.begin(115200);

    controllerSetup();
    spiSlaveSetup();

    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    spiSlaveProcess();

}
