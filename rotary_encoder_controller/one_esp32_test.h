//#include <Arduino.h>

#define LED_PIN 2

#define SENSOR_1_PIN_A 36
#define SENSOR_1_PIN_B 37
#define SENSOR_1_PIN_INDEX 38

#define SENSOR_2_PIN_A 39
#define SENSOR_2_PIN_B 34
#define SENSOR_2_PIN_INDEX 35

#define SIMUL_1_PIN_A 25
#define SIMUL_1_PIN_B 26
#define SIMUL_1_PIN_INDEX 27

#define SIMUL_2_PIN_A 14
#define SIMUL_2_PIN_B 12
#define SIMUL_2_PIN_INDEX 13

#define LED_PIN 2

#include "lib_rotary_encoder_controller_2.h"
#include "lib_simulator_test_2.h"
#include "lib_rotary_encoder_simulator_2.h"

RotarySensor rs1(SENSOR_1_PIN_A, SENSOR_1_PIN_B, SENSOR_1_PIN_INDEX, false, 4000, 10, (char*)"sensor1");
RotarySensor rs2(SENSOR_2_PIN_A, SENSOR_2_PIN_B, SENSOR_2_PIN_INDEX, false, 1000, 10, (char*)"sensor2");

RotarySensorSimulator rss1(&rs1, SIMUL_1_PIN_A, SIMUL_1_PIN_B, SIMUL_1_PIN_INDEX, true);
RotarySensorSimulator rss2(&rs2, SIMUL_2_PIN_A, SIMUL_2_PIN_B, SIMUL_2_PIN_INDEX, true);

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
    Serial.begin(115200);

    rs1.begin();
    rs2.begin();

    attachInterrupt(SENSOR_1_PIN_A, sensor1EventA, CHANGE);
    attachInterrupt(SENSOR_1_PIN_B, sensor1EventB, CHANGE);
    attachInterrupt(SENSOR_1_PIN_INDEX, sensor1EventIndex, RISING);

    attachInterrupt(SENSOR_2_PIN_A, sensor2EventA, CHANGE);
    attachInterrupt(SENSOR_2_PIN_B, sensor2EventB, CHANGE);
    attachInterrupt(SENSOR_2_PIN_INDEX, sensor2EventIndex, RISING);

    rss1.begin();
    rss2.begin();

    //controllerSetup();
    //simulatorSetup();

    pinMode(LED_PIN, OUTPUT);

    delay(2000);
}

int32_t simulationCount = 0, successCount = 0;

void loop() {
    //simul1.enabled = false;
    //simul2.enabled = false;

    delay(10);

    //Serial.println("Running simulation ...");
    // testModulo();

    // printSimulators();
    // printSensors();

    uint32_t periodInUs = 1;

    bool testFailed = false;

    rss1.index(periodInUs);
    testFailed |= !assertData("Reseting index", &rss1);
    rss2.index(periodInUs);
    testFailed |= !assertData("Reseting index", &rss2);
    
    // printSimulators();
    // printSensors();

    moveBothSimulators(&rss1, true, 0, &rss2, false, 1, periodInUs);
        
    // printSimulators();
    // printSensors();

    testFailed |= !assertData("Turning 0 steps", &rss1);
    testFailed |= !assertData("Turning 1 step left", &rss2);

    // printSimulators();
    // printSensors();


    moveBothSimulators(&rss1, true, 1, &rss2, false, 0, periodInUs);
    testFailed |= !assertData("Turning 1 steps right", &rss1);
    testFailed |= !assertData("Turning 0 step", &rss2);

    moveBothSimulators(&rss1, true, 1, &rss2, false, 1, periodInUs);
    testFailed |= !assertData("Turning 1 steps right", &rss1);
    testFailed |= !assertData("Turning 1 step left", &rss2);

    //printSensors();

    moveBothSimulators(&rss1, false, 2, &rss2, true, 3, periodInUs);
    testFailed = testFailed || !assertData("Turning 2 steps left", &rss1);
    testFailed = testFailed || !assertData("Turning 3 step right", &rss2);

    //printSensors();

    moveBothSimulators(&rss1, true, 3, &rss2, false, 2, periodInUs);
    testFailed = testFailed || !assertData("Turning 3 steps right", &rss1);
    testFailed = testFailed || !assertData("Turning 2 step left", &rss2);

    moveBothSimulators(&rss1, true, 11, &rss2, false, 7, periodInUs);
    testFailed = testFailed || !assertData("Turning 11 steps right", &rss1);
    testFailed = testFailed || !assertData("Turning 7 steps left", &rss2);
    
    moveBothSimulators(&rss1, true, 101, &rss2, true, 101, periodInUs);
    testFailed = testFailed || !assertData("Turning 101 steps right", &rss1);
    testFailed = testFailed || !assertData("Turning 101 steps right", &rss2);

    moveBothSimulators(&rss1, true, 3997, &rss2, false, 1001, periodInUs);
    testFailed = testFailed || !assertData("Turning 3997 steps right", &rss1);
    testFailed = testFailed || !assertData("Turning 1001 steps left", &rss2);
   
    // Turn 1 round one side
    moveBothSimulators(&rss1, true, rs1.getSensor()->maxPosition + 3, &rss2, false, rs2.getSensor()->maxPosition - 5, periodInUs);
    testFailed = testFailed || !assertData("Turning 1 round + 3 steps right", &rss1);
    testFailed = testFailed || !assertData("Turning 1 round - 5 steps right", &rss2);
    // printSimulators();
    // printSensors();

    testFailed |= !testPendulumWithAssertion(&rss1, rs1.getSensor()->maxPosition/2, &rss2, rs2.getSensor()->maxPosition/2, 12, periodInUs);

    // Turn 50 round one side
    //moveBothSimulators(true, sensor1.maxPosition * 50, false, sensor2.maxPosition * 50, periodInUs);
    //assertPosition("Turning 50 round right", sensor1, simul1);
    //assertPosition("Turning 50 round left", sensor2, simul2);

    // Reset index
    rss1.index(periodInUs);
    testFailed |= !assertData("Reseting index", &rss1);
    rss2.index(periodInUs);
    testFailed |= !assertData("Reseting index", &rss2);

    // Turn 20 round the other side
    moveBothSimulators(&rss1, false, rs1.getSensor()->maxPosition * 10 + 42, &rss2, true, rs2.getSensor()->maxPosition * 10 + 21, periodInUs);
    testFailed |= !assertData("Turning 10 round + 42 steps left", &rss1);
    testFailed |= !assertData("Turning 10 round + 21 steps right", &rss2);

    if (testFailed) {
        blinkLed();
    } else {
        successCount ++;
    }

    simulationCount ++;

    Serial.printf("Simulation #%d finished (%d global errors).\n", simulationCount, simulationCount - successCount);
}
