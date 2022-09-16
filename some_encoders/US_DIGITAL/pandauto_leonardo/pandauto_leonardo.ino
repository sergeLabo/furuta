
#include <Wire.h>
#include <AS5048A.h>

// 10 = SS
// false = no debug
AS5048A angleSensor(10, false);

const byte MY_ADDRESS = 42;
int val = 0;

void setup()
  {
  // Capteurs Panauto
  angleSensor.begin();

  Wire.begin (MY_ADDRESS);
  Wire.onRequest(requestEvent);
  }

void loop() {}

void requestEvent ()
  {
  int ang = angleSensor.getRotationInDegrees()*10;

  val = ang;
  byte buf [2];
  buf [0] = val >> 8;
  buf [1] = val & 0xFF;
  Wire.write (buf, 2);
  }
