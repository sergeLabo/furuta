#ifndef lib_rotary_encoder_simulator_h
#define lib_rotary_encoder_simulator_h

#include <Arduino.h>

#include "lib_utils.h"
#include "lib_model.h"
#include "lib_rotary_encoder_controller_2.h"

namespace rotaryEncoderSimulator {

    // 4 states
    void moveSimulator(AngleSensorSimulator* simulator, bool direction, uint32_t step, uint32_t periodInUs) {
        if (!simulator->enabled) {
            return;
        }
        //Serial.printf("[%s] Moving %d step in direction: %d with period of %d µs\n", simulator.name, step, direction, periodInUs);

        for(uint32_t k = 0; k < step; k++) {
            simulator->eventCount ++;

            if (direction) {
                // simulator->position ++;
                simulator->counter ++;
                simulator->internalState ++;
            } else {
                // simulator->position --;
                simulator->counter --;
                simulator->internalState --;
            }

            if (simulator->sensor->quadratureMode) {
                simulator->position = libutils::absMod16(simulator->counter, simulator->sensor->maxPosition);
            } else {
                simulator->position = libutils::absMod16(simulator->counter, simulator->sensor->maxPosition * 4) / 4;
            }
            
            uint16_t state = libutils::absMod16(simulator->internalState, 4);
            // Serial.printf("%s simulator new state: %d\n", simulator->name, state);
            // delay(1000);

            switch(state) {
                case 0:
                    gpio_set_level((gpio_num_t) simulator->pinA, LOW);
                    gpio_set_level((gpio_num_t) simulator->pinB, LOW);
                    //while(gpio_get_level((gpio_num_t) simulator->pinA) != LOW && (gpio_get_level((gpio_num_t) simulator->pinB) != LOW));
                    break;
                case 1:
                    gpio_set_level((gpio_num_t) simulator->pinA, LOW);
                    gpio_set_level((gpio_num_t) simulator->pinB, HIGH);
                    //while(gpio_get_level((gpio_num_t) simulator->pinA) != LOW && (gpio_get_level((gpio_num_t) simulator->pinB) != HIGH));
                    break;
                case 2:
                    gpio_set_level((gpio_num_t) simulator->pinA, HIGH);
                    gpio_set_level((gpio_num_t) simulator->pinB, HIGH);
                    //while(gpio_get_level((gpio_num_t) simulator->pinA) != HIGH && (gpio_get_level((gpio_num_t) simulator->pinB) != HIGH));
                    break;
                case 3:
                    gpio_set_level((gpio_num_t) simulator->pinA, HIGH);
                    gpio_set_level((gpio_num_t) simulator->pinB, LOW);
                    //while(gpio_get_level((gpio_num_t) simulator->pinA) != HIGH && (gpio_get_level((gpio_num_t) simulator->pinB) != LOW));
                    break;
                default:
                    // should not exists
                    Serial.printf("Bad simulator state: %d !!!\n", state);
            }
            delayMicroseconds(periodInUs);

            //printSensorInputs();
            //printSimulatorOutputs();
        }
    }

    void indexSimul(AngleSensorSimulator* simulator, uint32_t periodInUs) {
        //Serial.printf("[%s] Reseting index\n", simulator.name);
        simulator->position = 0;
        simulator->counter = 0;
        simulator->eventCount = 0;

        // digitalWrite(simulator.pinA, LOW);
        // digitalWrite(simulator.pinB, LOW);

        digitalWrite(simulator->pinIndex, HIGH);
        delayMicroseconds(periodInUs);
        digitalWrite(simulator->pinIndex, LOW);
    }
}

class RotarySensorSimulator {
private:
    AngleSensorSimulator simul;

public:
    
    RotarySensorSimulator(AngleSensor* sensor, uint8_t pinA, uint8_t pinB, uint8_t pinIndex, bool enabled) :
        simul({(AngleSensor*) sensor, pinA, pinB, pinIndex, 0, 0, 0, 0, enabled}) {
            begin();
        }
    
    RotarySensorSimulator(RotarySensor* rs, uint8_t pinA, uint8_t pinB, uint8_t pinIndex, bool enabled) :
        simul({rs->getSensor(), pinA, pinB, pinIndex, 0, 0, 0, 0, enabled}) {
            begin();
        }

    void begin() {
        pinMode(simul.pinA, OUTPUT);
        pinMode(simul.pinB, OUTPUT);
        pinMode(simul.pinIndex, OUTPUT);
        digitalWrite(simul.pinA, LOW);
        digitalWrite(simul.pinB, LOW);
        digitalWrite(simul.pinIndex, LOW);
    }

    void index(uint32_t periodInUs) {
        rotaryEncoderSimulator::indexSimul(&simul, periodInUs);
    }

    void move(bool direction, uint32_t step, uint32_t periodInUs) {
        rotaryEncoderSimulator::moveSimulator(&simul, direction, step, periodInUs);
    }

    AngleSensorSimulator* getSimulator() {
        return &simul;
    }
};

void moveBothSimulators(RotarySensorSimulator* rss1, bool direction1, uint32_t step1, RotarySensorSimulator* rss2, bool direction2, uint32_t step2, uint32_t periodInUs) {
    uint32_t maxStep = max(step1, step2);
    uint32_t minStep = min(step1, step2);
    uint32_t moves1 = 0;
    uint32_t moves2 = 0;
    for (; maxStep > 0; maxStep --) {
        if (minStep > 0) {
            // Do not wait period here
            if (step1 <= step2) {
                rss1->move(direction1, 1, 0);
                moves1 ++;
            } else {
                rss2->move(direction2, 1, 0);
                moves2 ++;
            }
            minStep --;
        }

        if (step1 > step2) {
            rss1->move(direction1, 1, 0);
            moves1 ++;
        } else {
            rss2->move(direction2, 1, 0);
            moves2 ++;
        }

        delayMicroseconds(periodInUs);
    }
    // Serial.printf("Moved simul1: %d ; simul2: %d\n", moves1, moves2);
}

#endif
