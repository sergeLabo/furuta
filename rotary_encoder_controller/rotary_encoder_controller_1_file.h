#include <Arduino.h>
#include <inttypes.h>

#define SENSOR_1_PIN_A 36
#define SENSOR_1_PIN_B 37
#define SENSOR_1_PIN_INDEX 38

#define SENSOR_2_PIN_A 39
#define SENSOR_2_PIN_B 34
#define SENSOR_2_PIN_INDEX 35

#define LED_PIN 2


int32_t absMod32(int32_t a, uint16_t b) {
    int32_t c = a % b;
    return (c < 0) ? c + b : c;
}

void initArray(int32_t* a) {
    size_t length = sizeof(a) / sizeof(a[0]);
    for (int8_t k = 0 ; k < length ; k ++) {
        a[k] = 0;
    }
}

int32_t printArray(char* buf, int32_t a[], int32_t size) {
    // Serial.printf("size: %d ", size);
    String message = "[";
    String data = String(a[0]);
    message.concat(data);
    for (int32_t k = 1; k < size; k ++) {
        message.concat("; ");
        String data = String(a[k]);
        message.concat(data);
    }
    message.concat("]");
    return sprintf(buf, message.c_str());
}

bool calcEvenParity(uint16_t payload) {
    //Serial.printf("payload: 0x%04x ; ", payload);

    // Exclude parity bit (Most Significatif Bit)
    byte bitCount = sizeof(payload) * 8;
    byte cnt = 0;
	byte i;

	for (i = 0; i < bitCount; i++) {
		if (payload & 0x1) {
			cnt ++;
		}
		payload >>= 1;
	}

    // Return 1 if odd number of 1 in payload
    bool result = cnt & 0x1;
    //Serial.printf("bitCount: %d ; parity: %d\n", bitCount, result);
    return result;
}

uint16_t paritize(uint16_t payload) {
    bool parity = calcEvenParity(payload);
    return payload | (parity << 15);
}


struct CircularBuffer {
  int32_t data[5]; // circular buffer
  int8_t offset;
  int8_t lastPosition;
  int32_t buffer[5]; // contains ordered data
};

size_t sizeCircularBuffer(CircularBuffer b) {
    size_t size = sizeof(b.data) / sizeof(b.data[0]);
    return size;
}

void pushCircularBuffer(CircularBuffer *b, int32_t data) {
    b->data[b->offset] = data;
    b->offset ++;
    b->lastPosition ++;

    size_t length = sizeof(b->data) / sizeof(b->data[0]);
    if (b->offset >= length) {
        b->offset = 0;
    }
    if (b->lastPosition >= length) {
        b->lastPosition = 0;
    }
}

void resetCircularBuffer(CircularBuffer *b) {
    size_t length = sizeof(b->data) / sizeof(b->data[0]);
    // for (int8_t k = 0 ; k < length; k++) {
    //     pushCircularBuffer(b, 0);
    // }
    initArray(b->data);
    b->offset = 0;
    b->lastPosition = length - 1;
}

int32_t getLastDataCircularBuffer(CircularBuffer b) {
    return b.data[b.lastPosition];
}

int32_t* getDataArrayCircularBuffer(CircularBuffer* b) {
    // Copy data array in new buffer: first item is last pushed
    size_t length = sizeof(b->data) / sizeof(b->data[0]);
    // Serial.printf("length: %d ", length);
    //int32_t* buffer = (int32_t *) malloc(length * sizeof(int32_t));
    int32_t* buffer = b->buffer;
    for (int32_t k = 0; k < 5; k ++) {
        int32_t index = b->lastPosition - k;
        if (index < 0) {
            index += length;
        }
        buffer[k] = b->data[index];
        // buf[k] = k + 1;
    }
    //length = sizeof(buffer) / sizeof(buffer[0]);
    // Serial.printf("length: %d ", length);
    return buffer;
}

int32_t printCircularBuffer(char* buf, CircularBuffer* b, bool newLine = true) {
    int32_t n = sprintf(buf, "CircularBuffer: ");
    int32_t* data = getDataArrayCircularBuffer(b);
    int32_t size = sizeCircularBuffer(*b);
    n += printArray(buf, data, size);
    if (newLine) {
        n += sprintf(buf, "\n");
    }
    return n;
}

struct AngleSensor {
    const uint8_t pinA;
    const uint8_t pinB;
    const uint8_t pinIndex;
    const uint16_t maxPosition;
    int32_t position;
    const char* name;
};

struct AngleSensorSimulator {
  const uint8_t pinA;
  const uint8_t pinB;
  const uint8_t pinIndex;
  int32_t position;
  int32_t counter;
  bool enabled;
  const char* name;
};

portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

CircularBuffer timings1;
CircularBuffer timings2;

AngleSensor sensor1 = {SENSOR_1_PIN_A, SENSOR_1_PIN_B, SENSOR_1_PIN_INDEX, 4000, 0, "sensor1"};
AngleSensor sensor2 = {SENSOR_2_PIN_A, SENSOR_2_PIN_B, SENSOR_2_PIN_INDEX, 1000, 0, "sensor2"};

void IRAM_ATTR moveSensor1A() {
    bool aLevel = digitalRead(sensor1.pinA);
    bool bLevel = digitalRead(sensor1.pinB);

    if (aLevel == bLevel) {
        // Increment position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings1, esp_timer_get_time());
        sensor1.position ++;
        portEXIT_CRITICAL(&mux);
    } else {
        // Decrement position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings1, -esp_timer_get_time());
        sensor1.position --;
        portEXIT_CRITICAL(&mux);
    }
    //sensor1.position = absMod32(sensor1.position, sensor1.maxPosition);
}

void IRAM_ATTR moveSensor1B() {
    bool aLevel = digitalRead(sensor1.pinA);
    bool bLevel = digitalRead(sensor1.pinB);

    if (aLevel != bLevel) {
        // Increment position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings1, esp_timer_get_time());
        sensor1.position ++;
        portEXIT_CRITICAL(&mux);
    } else {
        // Decrement position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings1, -esp_timer_get_time());
        sensor1.position --;
        portEXIT_CRITICAL(&mux);
    }
    //sensor1.position = absMod32(sensor1.position, sensor1.maxPosition);
}

void IRAM_ATTR resetSensor1() {
    portENTER_CRITICAL(&mux);
    sensor1.position = 0;
    portEXIT_CRITICAL(&mux);
}

void IRAM_ATTR moveSensor2A() {
    bool aLevel = digitalRead(sensor2.pinA);
    bool bLevel = digitalRead(sensor2.pinB);

    if (aLevel == bLevel) {
        // Increment position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings2, esp_timer_get_time());
        sensor2.position ++;
        portEXIT_CRITICAL(&mux);
    } else {
        // Decrement position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings2, -esp_timer_get_time());
        sensor2.position --;
        portEXIT_CRITICAL(&mux);
    }

    //sensor2.position = absMod32(sensor2.position, sensor2.maxPosition);
}

void IRAM_ATTR moveSensor2B() {
    bool aLevel = digitalRead(sensor2.pinA);
    bool bLevel = digitalRead(sensor2.pinB);

    if (aLevel != bLevel) {
        // Increment position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings2, esp_timer_get_time());
        sensor2.position ++;
        portEXIT_CRITICAL(&mux);
    } else {
        // Decrement position
        portENTER_CRITICAL(&mux);
        pushCircularBuffer(&timings2, -esp_timer_get_time());
        sensor2.position --;
        portEXIT_CRITICAL(&mux);
    }

    //sensor2.position = absMod32(sensor2.position, sensor2.maxPosition);
}

void IRAM_ATTR resetSensor2() {
    portENTER_CRITICAL(&mux);
    sensor2.position = 0;
    portEXIT_CRITICAL(&mux);
}


void printSensorInputs() {
    Serial.printf("INPUTS  [%s] pinA(%d): %d pinB(%d): %d pinIndex(%d): %d", sensor1.name, sensor1.pinA, digitalRead(sensor1.pinA), sensor1.pinB, digitalRead(sensor1.pinB), sensor1.pinIndex, digitalRead(sensor1.pinIndex));
    Serial.printf(" ; [%s] pinA(%d): %d pinB(%d): %d pinIndex(%d): %d\n", sensor2.name, sensor2.pinA, digitalRead(sensor2.pinA), sensor2.pinB, digitalRead(sensor2.pinB), sensor2.pinIndex, digitalRead(sensor2.pinIndex));
}

int32_t* calculateSpeeds(CircularBuffer* b, int64_t now) {
    int32_t* data = getDataArrayCircularBuffer(b);
    int32_t size = sizeCircularBuffer(*b);

    for (int32_t k = size - 1 ; k > 0 ; k --) {
        // Calculate instantaneous speed between timings
        if (data[k] > 0) {
            data[k] = abs(data[k - 1]) - data[k];
        } else {
            data[k] = - abs(data[k - 1]) - data[k];
        }
    }

    // Last speed is calculated with current time
    if (data[0] > 0) {
        data[0] = now - data[0];
    } else {
        data[0] = - now - data[0];
    }

    return data;
}

const char* positionMessage(AngleSensor sensor) {
    char* buf = (char*) malloc(sizeof(char) * 16);
    sprintf(buf, "%d", sensor.position);
    return buf;
}

int32_t speedMessage(char* buf, CircularBuffer* b, int64_t now) {
    int32_t size = sizeCircularBuffer(*b);
    int32_t* speeds = calculateSpeeds(b, now);
    return printArray(buf, speeds, size);
}

const char* sensorMessage(AngleSensor sensor, CircularBuffer* timings, int64_t now = esp_timer_get_time()) {
    char* buf = (char*) malloc(sizeof(char) * 128);
    int32_t n = sprintf(buf, "[%s] position: %d speeds: ", sensor.name, sensor.position);
    n += speedMessage(buf, timings, now);
    
    return buf;
}

int32_t sensorsMessage(char* buf) {
    // FIXME: probleme sur les overflow des timings.
    int64_t now = esp_timer_get_time();
    int32_t n = sprintf(buf, "[%s] position: %d speeds: ", sensor1.name, sensor1.position);
    n += speedMessage(&buf[n], &timings1, now);
    n += sprintf(&buf[n], " ; [%s] position: %d speeds: ", sensor2.name, sensor2.position);
    n += speedMessage(&buf[n], &timings2, now);
    return n;
}
/*
void printSpeeds(CircularBuffer* b, bool newLine = true) {
    String message = "speeds: %s";
    if (newLine) {
        message.concat("\n");
    }

    int32_t size = sizeCircularBuffer(*b);
    int32_t* speeds = calculateSpeeds(b);

    const char* timings = printArray(speeds, size);
    Serial.printf(message.c_str(), timings);
}
*/

void printSensor(AngleSensor sensor, CircularBuffer* timings, bool newLine = true) {
    const char* msg = sensorMessage(sensor, timings);
    Serial.printf("%s", msg);
    if (newLine) {
        Serial.println();
    }
}

char* sensorsMessageBuffer = (char*) malloc(sizeof(char) * 256);
void printSensors() {
    sensorsMessage(sensorsMessageBuffer);
    Serial.printf("%s\n", sensorsMessageBuffer);
}

void controllerSetup() {
    resetCircularBuffer(&timings1);
    resetCircularBuffer(&timings2);

    // Sensor 1
    pinMode(sensor1.pinA, INPUT_PULLUP);
    pinMode(sensor1.pinB, INPUT_PULLUP);
    pinMode(sensor1.pinIndex, INPUT_PULLUP);
    attachInterrupt(sensor1.pinA, moveSensor1A, CHANGE);
    attachInterrupt(sensor1.pinB, moveSensor1B, CHANGE);
    attachInterrupt(sensor1.pinIndex, resetSensor1, RISING);

    // Sensor 2
    pinMode(sensor2.pinA, INPUT_PULLUP);
    pinMode(sensor2.pinB, INPUT_PULLUP);
    pinMode(sensor2.pinIndex, INPUT_PULLUP);
    attachInterrupt(sensor2.pinA, moveSensor2A, CHANGE);
    attachInterrupt(sensor2.pinB, moveSensor2B, CHANGE);
    attachInterrupt(sensor2.pinIndex, resetSensor2, RISING);
}

void setup() {
    Serial.begin(115200);

    controllerSetup();

    pinMode(LED_PIN, OUTPUT);
}

void loop() {
    delay(100);

    printSensors();
}
