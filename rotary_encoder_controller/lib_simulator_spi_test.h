#ifndef lib_simulator_spi_test_h
#define lib_simulator_spi_test_h

#include <Arduino.h>

#include "lib_simulator_test.h"

void assertSpiPayload(const char* message, uint32_t pause = 0) {
    delayMicroseconds(100);
    bool valid = spiMasterProcess();
    if (valid) {
        //printDataPayload(spi_master_rx_buf, SPEEDS_COUNT_TO_KEEP);
    } else {
        blinkLed();
        Serial.printf("Invalid payload received for test: \"%s\" !\n", message);
        printDataPayload(spi_master_rx_buf, SPEEDS_COUNT_TO_KEEP);
        return;
    }

    uint16_t expectedPosition1 = absMod16(simul1.position, simul1.maxPosition);
    uint16_t expectedPosition2 = absMod16(simul2.position, simul2.maxPosition);

    uint16_t position1 = getPosition1(spi_master_rx_buf);
    uint16_t position2 = getPosition2(spi_master_rx_buf);

    bool doPause = false;
    if (position1 != expectedPosition1) {
        int32_t drift = abs(expectedPosition1 - position1);
        drift = min(drift, simul1.maxPosition - drift);
        Serial.printf("Bad position for sensor1 (%d step drift) expected %d but got %d \"%s\" !\n", drift, expectedPosition1, position1, message);
        doPause = true;
    }
    if (position2 != expectedPosition2) {
        int32_t drift = abs(expectedPosition2 - position2);
        drift = min(drift, simul2.maxPosition - drift);
        Serial.printf("Bad position for sensor2 (%d step drift) expected %d but got %d \"%s\" !\n", drift, expectedPosition2, position2, message);
        doPause = true;
    }

    if (doPause) {
        delay(pause);
    }
}

void testPendulumViaSpi(uint16_t amplitude1, uint16_t amplitude2, uint16_t bounces, uint32_t periodInUs, uint32_t failedTestPause) {
    indexSimul(&simul1, periodInUs);
    indexSimul(&simul2, periodInUs);
    for (; bounces > 0 ; bounces --) {
        moveBothSimulators(true, amplitude1, false, amplitude2, periodInUs);
        char message[60];
        sprintf(message, "Pendulum rising bounce %d", bounces);
        assertSpiPayload(message, failedTestPause);

        moveBothSimulators(false, amplitude1, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum falling bounce %d", bounces);
        assertSpiPayload(message, failedTestPause);

        indexSimul(&simul1, periodInUs);
        indexSimul(&simul2, periodInUs);
        assertSpiPayload("Indexing sensors", failedTestPause);

        amplitude1 -= (1/bounces) * amplitude1;
        amplitude2 -= (1/bounces) * amplitude2;
        moveBothSimulators(false, amplitude1, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum rising back bounce %d", bounces);
        assertSpiPayload(message, failedTestPause);

        moveBothSimulators(false, amplitude1, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum falling back bounce %d", bounces);
        assertSpiPayload(message, failedTestPause);

        indexSimul(&simul1, periodInUs);
        indexSimul(&simul2, periodInUs);
        assertSpiPayload("Indexing sensors", failedTestPause);
    }
}

#endif