#ifndef lib_simulator_test_h
#define lib_simulator_test_h

#include <Arduino.h>

#include "lib_model.h"
#include "lib_utils.h"
#include "lib_datagram.h"
#include "lib_rotary_encoder_simulator_2.h"

bool assertEventCount(const char* message, RotarySensorSimulator* rss, uint32_t got, uint32_t pause = 0) {
    const AngleSensorSimulator* simulator = rss->getSimulator();
    if (!simulator->enabled) {
        return true;
    }
    //delay(1);
    const AngleSensor* sensor = simulator->sensor;
    int32_t expected = (int32_t) rss->getSimulator()->eventCount;
    int32_t drift = abs(expected - got);
    
    if (drift > 0) {
        Serial.printf("Bad event count for [%s] (%d step drift) expected %d but got %d \"%s\" !\n", sensor->name, drift, expected, got, message);
        delay(pause);
    }

    return drift == 0;
}

bool assertCount(const char* message, RotarySensorSimulator* rss, int32_t got, uint32_t pause = 0) {
    const AngleSensorSimulator* simulator = rss->getSimulator();
    if (!simulator->enabled) {
        return true;
    }
    //delay(1);
    const AngleSensor* sensor = simulator->sensor;
    int32_t expected = simulator->counter;
    int32_t drift = abs(expected - got);

    if (drift > 0) {
        Serial.printf("Bad count for [%s] (%d step drift) expected %d but got %d \"%s\" !\n", sensor->name, drift, expected, got, message);
        delay(pause);
    }

    return drift == 0;
}

bool assertPosition(const char* message, RotarySensorSimulator* rss, uint16_t got, uint32_t pause = 0) {
    const AngleSensorSimulator* simulator = rss->getSimulator();
    if (!simulator->enabled) {
        return true;
    }
    //delay(1);
    const AngleSensor* sensor = simulator->sensor;
    uint16_t expected = simulator->position;
    uint16_t drift = abs(expected - got);
    drift = min(drift, (uint16_t) (sensor->maxPosition - drift));

    if (drift > 0) {
        Serial.printf("Bad position for [%s] (%d step drift) expected %d but got %d \"%s\" !\n", sensor->name, drift, expected, got, message);
        delay(pause);
    }

    return drift == 0;
}

bool assertData(const char* message, RotarySensorSimulator* rss, uint16_t gotPosition, int32_t gotCount, uint32_t gotEventCount, uint32_t pause = 0) {
    if (!rss->getSimulator()->enabled) {
        return true;
    }
    bool test = assertPosition(message, rss, gotPosition, 0);
    test = assertCount(message, rss, gotCount, 0) && test;
    //test = assertEventCount(message, sensor, simulator, 0) && test;
    assertEventCount(message, rss, gotEventCount, 0); // If event count drifted it not necessarily an error.

    if (!test) {
        //blinkLed();
        delay(pause);
    }

    return test;
}

bool assertData(const char* message, RotarySensorSimulator* rss, uint32_t pause = 0) {
    uint16_t gotPosition = rss->getSimulator()->sensor->position;
    int32_t gotCount = rss->getSimulator()->sensor->counter;
    uint32_t gotEventCount = rss->getSimulator()->sensor->eventCount;
    return assertData(message, rss, gotPosition, gotCount, gotEventCount, pause);
}

void testModulo() {
    int16_t a = -1;
    uint16_t b = 4000;
    uint16_t c = libutils::absMod16(a, b);
    Serial.printf("%d absMod16 %d = %d\n", a, b, c);

    a = -1;
    c = libutils::absMod16(a, b);
    Serial.printf("%d absMod16 %d = %d\n", a, b, c);

    a = -4001;
    c = libutils::absMod16(a, b);
    Serial.printf("%d absMod16 %d = %d\n", a, b, c);

    a = 4000;
    c = libutils::absMod16(a, b);
    Serial.printf("%d absMod16 %d = %d\n", a, b, c);

    a = 4001;
    c = libutils::absMod16(a, b);
    Serial.printf("%d absMod16 %d = %d\n", a, b, c);
}

bool testPendulumWithAssertion(RotarySensorSimulator* rss1, uint16_t amplitude1, RotarySensorSimulator* rss2, uint16_t amplitude2, uint16_t bounces, uint32_t periodInUs) {
    bool testFailed = false;

    rss1->index(periodInUs);
    rss2->index(periodInUs);
    for (; bounces > 0 ; bounces --) {
        bool failed1 = false, failed2 = false;
        moveBothSimulators(rss1, true, amplitude1, rss2, false, amplitude2, periodInUs);
        char message[60];
        sprintf(message, "Pendulum rising bounce %d", bounces);
        failed1 = !assertData(message, rss1) || testFailed;
        failed2 = !assertData(message, rss2) || testFailed;

        moveBothSimulators(rss1, false, amplitude1, rss2, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum falling bounce %d", bounces);
        failed1 = failed1 || !assertData(message, rss1);
        failed2 = failed2 || !assertData(message, rss2);

        rss1->index(periodInUs);
        sprintf(message, "Reseting index falling bounce %d", bounces);
        failed1 |= !assertData(message, rss1);
        rss2->index(periodInUs);
        failed2 |= !assertData(message, rss2);

        amplitude1 -= ((float)1/bounces) * amplitude1;
        amplitude2 -= ((float)1/bounces) * amplitude2;
        moveBothSimulators(rss1, false, amplitude1, rss2, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum rising back bounce %d", bounces);
        failed1 |= !assertData(message, rss1);
        failed2 |= !assertData(message, rss2);

        moveBothSimulators(rss1, false, amplitude1, rss2, true, amplitude2, periodInUs);
        sprintf(message, "Pendulum falling back bounce %d", bounces);
        failed1 = failed1 || !assertData(message, rss1);
        failed2 = failed2 || !assertData(message, rss2);

        rss1->index(periodInUs);
        sprintf(message, "Reseting index falling back bounce %d", bounces);
        failed1 |= !assertData(message, rss1);
        rss2->index(periodInUs);
        failed2 |= !assertData(message, rss2);

        testFailed |= failed1 || failed2;
    }
    return !testFailed;
}

#endif