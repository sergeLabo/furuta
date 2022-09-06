
#include <Wire.h>

const int SLAVE_ADDRESS = 42;

// various commands we might send
enum {
    CMD_ID = 1,
    CMD_READ_A0  = 2,
    CMD_READ_D8 = 3
    };

void sendCommand (const byte cmd, const int responseSize)
  {
  Wire.beginTransmission (SLAVE_ADDRESS);
  Wire.write (cmd);
  Wire.endTransmission ();
  
  Wire.requestFrom (SLAVE_ADDRESS, responseSize);  
  }  // end of sendCommand
  
void setup ()
  {
  Wire.begin ();   
  Serial.begin (9600);  // start serial for output
  
  sendCommand (CMD_ID, 1);
  
  if (Wire.available ())
    {
    Serial.print ("Slave is ID: ");
    Serial.println (Wire.read (), DEC);
    }
  else
    Serial.println ("No response to ID request");
  
  }  // end of setup

void loop()
  {
  int val;
  
  sendCommand (CMD_READ_A0, 2);
  val = Wire.read ();
  val <<= 8;
  val |= Wire.read ();
  Serial.print ("Value of A0: ");
  Serial.println (val, DEC);

  sendCommand (CMD_READ_D8, 1);
  val = Wire.read ();
  Serial.print ("Value of D8: ");
  Serial.println (val, DEC);

  delay (500);   
  }  // end of loop
