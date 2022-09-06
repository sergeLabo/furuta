// Written by Nick Gammon
// Date: 18th February 2011

// sergeLabo: plus simple

#include <Wire.h>

const byte MY_ADDRESS = 42;

int val = 0;
int command = 0;

void setup()
  {
  Serial.begin(9600);
  Wire.begin (MY_ADDRESS);
  // interrupt handler for incoming messages
  Wire.onReceive (receiveEvent);
  // interrupt handler for when data is wanted
  Wire.onRequest (requestEvent);
  }

void loop()
  {
  val++;
  if (val > 3000) {
    val = 0;
    }
  delay(100);
  }

void receiveEvent (int howMany) // howMany received bytes number
  {
  // remember command for when we get request
  int command = Wire.read ();
  Serial.print("receive ");
  Serial.print(howMany);
  Serial.print(" bytes:  ");
  Serial.println(command);
  sendSensor();
  }

void sendSensor ()
  {
  Serial.print("Send: ");
  Serial.println(val);
  // Send 2 bytes idem est 0< number < ~32000
  byte buf [2];
    buf [0] = val >> 8;
    buf [1] = val & 0xFF;
    Wire.write (buf, 2);
  }

void requestEvent ()
  {
  Serial.print("request ");
  if (command == 0) {
      Serial.println("La demande est 0");
      }
  if (command == 1) {
      Serial.println("La demande est 1");
      sendSensor();
     }
  }
