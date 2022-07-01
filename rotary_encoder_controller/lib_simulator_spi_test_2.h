#ifndef lib_simulator_spi_test_h
#define lib_simulator_spi_test_h

#include <Arduino.h>

#include "lib_simulator_test_2.h"
#include "lib_rotary_encoder_simulator_2.h"
#include "lib_rotary_encoder_controller_spi_master_2.h"

bool assertSpiPayload(const char* message, RotarySensorSimulator* rss1, RotarySensorSimulator* rss2, uint32_t pause = 0) {
    bool valid = spiMasterProcess();
    if (valid) {
        //printDataPayload(spi_master_rx_buf, SPEEDS_COUNT_TO_KEEP);
    } else {
        libutils::blinkLed();
        Serial.printf("Invalid payload received for test: \"%s\" !\n", message);
        printDataPayload(spi_master_rx_buf, SPEEDS_COUNT_TO_KEEP);
        return false;
    }

    uint16_t maxPosition1 = rss1->getSimulator()->sensor->maxPosition;
    uint16_t maxPosition2 = rss2->getSimulator()->sensor->maxPosition;
    uint16_t expectedPosition1 = rss1->getSimulator()->position;
    uint16_t expectedPosition2 = rss2->getSimulator()->position;

    uint16_t gotPosition1 = getPosition1(spi_master_rx_buf);
    uint16_t gotPosition2 = getPosition2(spi_master_rx_buf);

    bool failedTest = false;
    if (gotPosition1 != expectedPosition1) {
        int32_t drift = abs(expectedPosition1 - gotPosition1);
        drift = min(drift, maxPosition1 - drift);
        Serial.printf("Bad position for sensor1 (%d step drift) expected %d but got %d \"%s\" !\n", drift, expectedPosition1, gotPosition1, message);
        failedTest = true;
    }
    if (gotPosition2 != expectedPosition2) {
        int32_t drift = abs(expectedPosition2 - gotPosition2);
        drift = min(drift, maxPosition2 - drift);
        Serial.printf("Bad position for sensor2 (%d step drift) expected %d but got %d \"%s\" !\n", drift, expectedPosition2, gotPosition2, message);
        failedTest = true;
    }

    if (failedTest) {
        delay(pause);
    }

    return failedTest;
}

bool testPendulumViaSpi(RotarySensorSimulator* rss1, uint16_t amplitude1, RotarySensorSimulator* rss2, uint16_t amplitude2, uint16_t bounces, uint32_t periodInUs, uint32_t failedTestPause) {
    bool testFailed = false;

    rss1->index(periodInUs);
    rss2->index(periodInUs);
    for (; bounces > 0 ; bounces --) {
        // bool failed1 = false, failed2 = false;
        bool failed = false;
        moveBothSimulators(rss1, true, amplitude1, rss2, false, amplitude2, periodInUs);
        char message[60];
        sprintf(message, "Pendulum rising bounce %d", bounces);
        // failed1 = !assertData(message, rss1) || testFailed;
        // failed2 = !assertData(message, rss2) || testFailed;
        failed = !assertSpiPayload(message, rss1, rss2, failedTestPause);

        moveBothSimulators(rss1, false, amplitude1, rss2, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum falling bounce %d", bounces);
        // failed1 = failed1 || !assertData(message, rss1);
        // failed2 = failed2 || !assertData(message, rss2);
        failed = failed || assertSpiPayload(message, rss1, rss2, failedTestPause);

        rss1->index(periodInUs);
        sprintf(message, "Reseting index falling bounce %d", bounces);
        rss2->index(periodInUs);
        // failed1 |= !assertData(message, rss1);
        // failed2 |= !assertData(message, rss2);
        failed |= assertSpiPayload(message, rss1, rss2, failedTestPause);

        amplitude1 -= ((float)1/bounces) * amplitude1;
        amplitude2 -= ((float)1/bounces) * amplitude2;
        moveBothSimulators(rss1, false, amplitude1, rss2, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum rising back bounce %d", bounces);
        // failed1 |= !assertData(message, rss1);
        // failed2 |= !assertData(message, rss2);
        failed |= assertSpiPayload(message, rss1, rss2, failedTestPause);

        moveBothSimulators(rss1, false, amplitude1, rss2, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum falling back bounce %d", bounces);
        // failed1 = failed1 || !assertData(message, rss1);
        // failed2 = failed2 || !assertData(message, rss2);
        failed = failed || assertSpiPayload(message, rss1, rss2, failedTestPause);

        rss1->index(periodInUs);
        sprintf(message, "Reseting index falling back bounce %d", bounces);
        rss2->index(periodInUs);
        // failed1 |= !assertData(message, rss1);
        // failed2 |= !assertData(message, rss2);
        failed |= assertSpiPayload(message, rss1, rss2, failedTestPause);

        // testFailed |= failed1 || failed2;
        testFailed |= failed;
    }
    return !testFailed;
}

#endif