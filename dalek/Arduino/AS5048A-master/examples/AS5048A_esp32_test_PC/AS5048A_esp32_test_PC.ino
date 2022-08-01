
#include <AS5048A.h>

// SS device select true = debug
AS5048A angleSensor(2, true);



void setup()
{
    Serial.begin(19200);
    angleSensor.begin();
}

void loop()
{
    delay(1000);

    float val = angleSensor.getRotationInDegrees();
    Serial.print("\nGot rotation of: ");
    Serial.println(val);
    Serial.print("State: ");
    angleSensor.printState();
    Serial.print("Errors: ");
    Serial.println(angleSensor.getErrors());
}
