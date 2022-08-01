#include <AS5048A.h>

//SPI.usingInterrupt(7)
//#define PIN_SPI_SS (7)
//#define SDCARD_SS_PIN 4

AS5048A angleSensor(10);


void setup()
{
	Serial.begin(115200);
	angleSensor.init();
}

void loop()
{
	delay(10);
	word val = angleSensor.getRawRotation();
  Serial.println(val, DEC); 
}
