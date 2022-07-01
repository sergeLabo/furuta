#include <Arduino.h>

#define SPI_MISO (gpio_num_t) 19
#define SPI_MOSI (gpio_num_t) 23
#define SPI_CLK (gpio_num_t) 18
#define SPI_CS   (gpio_num_t) 22

#define SENSOR_1_PIN_A (gpio_num_t) 34
#define SENSOR_1_PIN_B (gpio_num_t) 35
#define SENSOR_1_PIN_INDEX (gpio_num_t) 15

#define SENSOR_2_PIN_A (gpio_num_t) 16
#define SENSOR_2_PIN_B (gpio_num_t) 4
#define SENSOR_2_PIN_INDEX (gpio_num_t) 12

#define LED_PIN (gpio_num_t) 5

//#define LOG_INFO
//#define LOG_WARN

#include "rotary_encoder_config.h"
#include "lib_rotary_encoder_controller_2.h"
#include "lib_rotary_encoder_controller_spi_slave_2.h"

RotarySensor rs1(SENSOR_1_PIN_A, SENSOR_1_PIN_B, SENSOR_1_PIN_INDEX, true, 4000, 10, (char*)"sensor1");
RotarySensor rs2(SENSOR_2_PIN_A, SENSOR_2_PIN_B, SENSOR_2_PIN_INDEX, true, 4000, 10, (char*)"sensor2");

void IRAM_ATTR sensor1EventA() {
    rs1.eventA();
}

void IRAM_ATTR sensor1EventB() {
    rs1.eventB();
}

void IRAM_ATTR sensor1EventIndex() {
    rs1.eventIndex();
}

void IRAM_ATTR sensor2EventA() {
    rs2.eventA();
}

void IRAM_ATTR sensor2EventB() {
    rs2.eventB();
}

void IRAM_ATTR sensor2EventIndex() {
    rs2.eventIndex();
}

void setup() {
    //Serial.begin(115200);

    rs1.begin();
    rs2.begin();

    attachInterrupt(SENSOR_1_PIN_A, sensor1EventA, CHANGE);
    attachInterrupt(SENSOR_1_PIN_B, sensor1EventB, CHANGE);
    attachInterrupt(SENSOR_1_PIN_INDEX, sensor1EventIndex, RISING);

    attachInterrupt(SENSOR_2_PIN_A, sensor2EventA, CHANGE);
    attachInterrupt(SENSOR_2_PIN_B, sensor2EventB, CHANGE);
    attachInterrupt(SENSOR_2_PIN_INDEX, sensor2EventIndex, RISING);

    spiSlaveSetup();

    pinMode(LED_PIN, OUTPUT);

    delay(2000);
}

void loop() {
    spiSlaveProcess(&rs1, &rs2);
}
