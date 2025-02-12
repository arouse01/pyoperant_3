#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
/*
 * Revision 1.1
 * 2/23/18 by Andrew Rouse
 * 
 */

/*
Pins used:
Set by Teensyduino:
//6 - Audio shield, MEMCS (NOT USED)
7 - Audio shield, MOSI (SD, shared)
9 - Audio shield, BCLK*
10 - Audio shield, CS (SD)
11 - Audio shield, MCLK*
12 - Audio shield, MISO (SD, shared)
13 - Audio shield, RX*
14 - Audio shield, SCLK (SD)
18 - Audio shield, SDA*
19 - Audio shield, SCL*
22 - Audio shield, TX*
23 - Audio shield, LRCLK*

Set by pyoperant:
1 - trial light
2 - overhead light relay
3 - response light
16 - reinforcement relay
37 - response sensor
38 - start sensor

*/

// -----

static uint8_t myID[8]; //for getting unique Teensy ID
unsigned long serialNum = 0; //for getting Teensy serial number - not sure which to use, serialNum or myID


int inputValue = 0;
int baudRate = 19200;
char ioBytes[2];
int ioPort = 0;

// Audio setup
// Includes audio input and output
// GUItool: begin automatically generated code
AudioInputI2S            i2s2;           //xy=292,151
AudioInputUSB            usb1;           //xy=293,190
AudioOutputUSB           usb2;           //xy=545,150
AudioOutputI2S           i2s1;           //xy=547,189
AudioConnection          patchCord1(i2s2, 0, usb2, 0);
AudioConnection          patchCord2(i2s2, 1, usb2, 1);
AudioConnection          patchCord3(usb1, 0, i2s1, 0);
AudioConnection          patchCord4(usb1, 1, i2s1, 1);
AudioControlSGTL5000     sgtl5000_1;     //xy=448,283
// GUItool: end automatically generated code


// /*
// Code for getting Teensy unique ID # (so log files can accurately reflect which unit they came from)
// */
// void read_EE(uint8_t word, uint8_t *buf, uint8_t offset)  {
//   noInterrupts();
//   FTFL_FCCOB0 = 0x41;             // Selects the READONCE command
//   FTFL_FCCOB1 = word;             // read the given word of read once area

//   // launch command and wait until complete
//   FTFL_FSTAT = FTFL_FSTAT_CCIF;
//   while(!(FTFL_FSTAT & FTFL_FSTAT_CCIF))
//     ;
//   *(buf+offset+0) = FTFL_FCCOB4;
//   *(buf+offset+1) = FTFL_FCCOB5;       
//   *(buf+offset+2) = FTFL_FCCOB6;       
//   *(buf+offset+3) = FTFL_FCCOB7;       
//   interrupts();
// }

    
// void read_myID() {
//   read_EE(0xe,myID,0); // should be 04 E9 E5 xx, this being PJRC's registered OUI
//   read_EE(0xf,myID,4); // xx xx xx xx
  
//   unsigned int ii;
//   for (ii = 0; ii < sizeof(myID); ii++) {
//     if ( ii > 3)
//       serialNum = (serialNum << 8) + myID[ii];
//   }
// }


void setup(){
  Serial.begin(baudRate);
  while (!Serial) {
    ; // wait for serial port to connect
  }
  Serial.printf("Connected to Teensy");
  
  // read_myID();
  // Serial.printf("Teensy ID %d0 \n \n", serialNum);
  
  AudioMemory(12);
  sgtl5000_1.enable();
  sgtl5000_1.volume(0.4);
  
}

void loop() {
  // All serial communications should be two bytes long
  // The first byte specifies the port to act on
  // The second byte specifies the action to take
  // The actions are:
  // 0: Read the specified input
  // 1: Write the specified output to HIGH
  // 2: Write the specified output to LOW
  // 3: Set the specified pin to OUTPUT
  // 4: Set the specified pin to INPUT
  // 5: Set the specified pin to INPUT_PULLUP
  // 6: Return Teensy ID number (pin independent)
  // 99: Audio control (pin independent)
  // if we get a valid serial message, read the request:
  if (Serial.available() >= 2) {
    // get incoming three bytes:
    Serial.readBytes(ioBytes, 2);
//    Serial.println("I received: ");
//    Serial.println(ioBytes[0], DEC);
//    Serial.println(ioBytes[1], DEC);
    // Extract the specified port
    ioPort = (int) ioBytes[0];
//  if (ioPort == 99) {
//    // 99 is for audio functions
//    if (ioBytes[1] == 0) {
//      //Stop playback
//      playSdRaw1.stop();  
//      break;
//    }
//    else if (ioBytes[1] == 1) {
//        //Selected type is S+, choose file
//        //randNumber = random(1,length(s+List))
//        //const char *filename = S+filelist[filenumber];
//    }
//    else if (ioBytes[1] == 2) {
//        //Selected type is S-, choose file
//        //randNumber = random(1,length(s-List))
//        //const char *filename = S-filelist[filenumber];
//    }   
//    //Could add additional types here
//    
//    playSdRaw1.play(filename);
//    break;
//  }
//
//  else
    // Specific pin actions 
    
    // Switch case on the specified action
    switch ((int) ioBytes[1]) {
      case 0: // Read an input
      inputValue = digitalRead(ioPort);
      Serial.write(inputValue);
      break;
      case 1: // Write an output to HIGH
      digitalWrite(ioPort, HIGH);       
      break;
      case 2: // Write an output to LOW
      digitalWrite(ioPort, LOW);        
      break;
      case 3: // Set a pin to OUTPUT
      pinMode(ioPort, OUTPUT);
      digitalWrite(ioPort, LOW);
      break;
      case 4: // Set a pin to INPUT
      pinMode(ioPort, INPUT);
      break;
      case 5: // Set a pin to INPUT_PULLUP
      pinMode(ioPort, INPUT_PULLUP);
      break;
      case 6: // Return Teensy ID
      Serial.write("Teensy ID: ");
      Serial.write(serialNum);
      break;
    //}
    }
  }
}





