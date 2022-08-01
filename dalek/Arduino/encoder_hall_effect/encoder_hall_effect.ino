// Written by Nick Gammon
// April 2011
// How_to_get_a_response_from_a_slave modified to
// encoder_hall_effect


#include <SPI.h>

void setup (void)
{
    Serial.begin (19200);
    Serial.println("Hall Effect Encoder");

    digitalWrite(SS, HIGH);  // ensure SS stays high for now

    // Put SCK, MOSI, SS pins into output mode
    // also put SCK, MOSI into LOW state, and SS into HIGH state.
    // Then put SPI hardware into Master mode and turn SPI on
    SPI.begin ();

    //bitSet(SPCR, 4);                //UNO_1 is Master
    //SPI.setBitOrder(MSBFIRST);      //bit transmission order
    //SPI.setDataMode(SPI_MODE0);     // Setup at RE and Saple at FE
    SPI.setClockDivider(SPI_CLOCK_DIV8);

    // disable Slave Select
    //digitalWrite(SS, HIGH);
    delay (100);

}  // end of setup

byte transferAndWait(const byte what)
{
  byte a = SPI.transfer (what);
  delayMicroseconds (20);
  return a;
} // end of transferAndWait

byte transfer(const byte what)
{
  byte a = SPI.transfer (what);
  return a;
}

void loop (void)
{
    byte a;

    digitalWrite(SS, LOW);
    delay (100);

    byte command = 0xBB;
    a = SPI.transfer(command);

    Serial.println(a);

    // enable Slave Select
    digitalWrite(SS, HIGH);

    delay (1000);  // 0.1 second delay
}  // end of loop
