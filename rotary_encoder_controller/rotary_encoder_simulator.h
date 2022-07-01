#include <Arduino.h>

#define SPI_MISO 19
#define SPI_MOSI 23
#define SPI_CLK 18
#define SPI_CS   5

#define SIMUL_1_PIN_A 16
#define SIMUL_1_PIN_B 4
#define SIMUL_1_PIN_INDEX 0

#define SIMUL_2_PIN_A 27
#define SIMUL_2_PIN_B 14
#define SIMUL_2_PIN_INDEX 12

#define LED_PIN 22

#define LOG_WARN
#define LOG_INFO

#include "rotary_encoder_config.h"
#include "lib_rotary_encoder_simulator_2.h"
#include "lib_rotary_encoder_controller_spi_master_2.h"
#include "lib_simulator_test_2.h"
#include "lib_simulator_spi_test_2.h"
#include "lib_datagram.h"

RotarySensor rs1(0, 0, 0, false, 4000, 10, (char*)"sensor1");
RotarySensor rs2(0, 0, 0, false, 1000, 10, (char*)"sensor2");

RotarySensorSimulator rss1(&rs1, SIMUL_1_PIN_A, SIMUL_1_PIN_B, SIMUL_1_PIN_INDEX, true);
RotarySensorSimulator rss2(&rs2, SIMUL_2_PIN_A, SIMUL_2_PIN_B, SIMUL_2_PIN_INDEX, true);

void setup() {
    Serial.begin(115200);

    //simulatorSetup();
    spiMasterSetup();

    pinMode(LED_PIN, OUTPUT);

    delay(2000);
}

uint8_t* messageBuffer = (uint8_t*) malloc(sizeof(uint8_t) * SPI_WORD_SIZE);
int32_t simulationCount = 0, successCount = 0;

void loop() {
    delay(10);

    bool testFailed = false;

    //Serial.println("Running simulation ...");
    int64_t startTime = esp_timer_get_time();
    // testModulo();

    // printSimulators();
    // printSensors();

    uint32_t periodInUs = 10;
    uint32_t failedTestPause = 0;

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    testFailed |= assertSpiPayload("Indexing sensors", &rss1, &rss2, failedTestPause);

    moveBothSimulators(&rss1, true, 0, &rss2, false, 1, periodInUs);
    testFailed |= assertSpiPayload("Turning 1 step left (s2)", &rss1, &rss2, failedTestPause);

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, true, 1, &rss2, false, 0, periodInUs);
    testFailed |= assertSpiPayload("Turning 1 step right (s1)", &rss1, &rss2, failedTestPause);

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, true, 1, &rss2, false, 1, periodInUs);
    testFailed |= assertSpiPayload("Turning 1 step right (s1) and 1 step left (s2)", &rss1, &rss2, failedTestPause);

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, false, 2, &rss2, true, 3, periodInUs);
    testFailed |= assertSpiPayload("Turning 2 step left (s1) and 3 step right (s2)", &rss1, &rss2, failedTestPause);

    moveBothSimulators(&rss1, true, 3, &rss2, false, 2, periodInUs);
    testFailed |= assertSpiPayload("Turning 3 step right (s1) and 2 step left (s2)", &rss1, &rss2, failedTestPause);

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, true, 11, &rss2, false, 7, periodInUs);
    testFailed |= assertSpiPayload("Turning 11 steps right (s1) and 7 steps left (s2)", &rss1, &rss2, failedTestPause);

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, true, 101, &rss2, true, 101, periodInUs);
    testFailed |= assertSpiPayload("Turning 101 steps right (s1) and 101 steps right (s2)", &rss1, &rss2, failedTestPause);

    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, true, 3997, &rss2, false, 1001, periodInUs);
    testFailed |= assertSpiPayload("Turning 3997 steps right (s1) and 1001 steps left (s2)", &rss1, &rss2, failedTestPause);
   
    // Turn 1 round one side
    rss1.index(periodInUs);
    rss2.index(periodInUs);
    moveBothSimulators(&rss1, true, 4003, &rss2, false, 995, periodInUs);
    testFailed |= assertSpiPayload("Turning 4003 steps right (s1) and 995 steps left (s2)", &rss1, &rss2, failedTestPause);

    testFailed |= testPendulumViaSpi(&rss1, 2000, &rss2, 500, 12, periodInUs, failedTestPause);

    moveBothSimulators(&rss1, true, 3, &rss2, false, 3, periodInUs);
    testFailed |= assertSpiPayload("Turning 3 step right (s1) and 2 step left (s2)", &rss1, &rss2, failedTestPause);

    // Print last data payload
    //printDataPayload(spi_master_rx_buf, SPEEDS_COUNT_TO_KEEP);

    int64_t endTime = esp_timer_get_time();
    int32_t duration = (int32_t) (endTime - startTime);

    if (! testFailed) {
        successCount ++;
    }

    simulationCount ++;

    Serial.printf("Simulation #%d took %d µs (%d global errors).\n", simulationCount, duration, simulationCount - successCount);
}