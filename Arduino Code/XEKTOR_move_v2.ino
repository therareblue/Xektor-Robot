#include <Wire.h>

#define LFW 5
#define RFW 6
#define LBW 9
#define RBW 10

#define LdF 7 //left led forwards
#define LdB 8 //left led backwards
#define RdF 16
#define RdB 14


byte dur = 0;
int Lspd, Rspd = 0;
unsigned long last_run = 0;
int run_int = 100; //duration of 1 run sample is 0.1 seconds. If dur = 5, time of operation = 5 * run_int = 0.5 seconds.
//byte answ = 0;
byte ismovin = 0; //shows wheither the motors are moving or not
//LED
int lint, rint = 0; //LED interval of on/off for left and right led /in miliseconds/ 1000ms = 1s
unsigned long llast, rlast = 0; //last time LED was on
bool ledon, lflag, rflag = false; //flag ledon shows the leds that the motors is now running, so they will start flashing.

void setup() {
  pinMode(LFW, OUTPUT);
  pinMode(RFW, OUTPUT);
  pinMode(LBW, OUTPUT);
  pinMode(RBW, OUTPUT);
  delay(100);
  analogWrite(LFW, 0);
  analogWrite(RFW, 0);
  analogWrite(LBW, 0);
  analogWrite(RBW, 0);

  pinMode(LdF, OUTPUT);
  pinMode(RdF, OUTPUT);
  pinMode(LdB, OUTPUT);
  pinMode(RdB, OUTPUT);
  delay(100);
  digitalWrite(LdF, LOW);
  digitalWrite(RdF, LOW);
  digitalWrite(LdB, LOW);
  digitalWrite(RdB, LOW);

  Wire.begin(0x04);
  delay(50);
  Wire.onReceive(receiveit);
  Wire.onRequest(sendit);
}

void receiveit(){
  byte instr[2]; //data from i2c, [0] is motorN, forw/back (0, 1,2,3,4); 0 byte is duration in 0.1 seconds (value 0-255 * 0.1) in seconds of duration
  int i=0;
  while (Wire.available()){
    byte c = Wire.read();
    instr[i] = c;
    i++;
  }
  Serial.print("an instruction is received:");
  Serial.print("[");Serial.print(instr[0]);Serial.print(",");Serial.print(instr[1]);Serial.println("]");

  // instructions explained:
  // first the speed of both motors is received. if the speed is not received, the controller use the last used speed data
  // next the 0 byte is received, saying to the board to perform the move. the 0 byte have the duration parameter, from 0 to 255, in 0.1sec, each.
  // if the 0 byte is not 0, a duration is calculated and the movement is performed.
  // after duration is exceeded, the 0 byte becomes = 0 which will say the motors to stop moving.

  switch(instr[0]){
    case 0:
      {if (dur == 255) dur = 10000; //if an instruction 255 is received, it will drive continuously (actually 16.6 minutes) until stop instruction is received
       else dur = instr[1];
      }break;
    case 1:
      {Lspd = instr[1];
      }break;
    case 2:
      {Rspd = instr[1];
      }break;
    case 3:
      {Lspd = -instr[1];
      }break;
    case 4:
      {Rspd = -instr[1];
      }break;
  }

  //calculate the interval of blinkink of the motor leds:
  int abss = 0; float calc = 0;
  if (Lspd == 0) lint = 0;
  else{abss = abs(Lspd); calc = abss/255.0; lint = int(1000 - (900*calc));}
  if (Rspd == 0) rint = 0;
  else{abss = abs(Rspd); calc = abss/255.0; rint = int(1000 - (900*calc));} 

  //Serial.print("lint = ");Serial.print(lint); Serial.print(" | rint = ");Serial.print(rint);Serial.println("]");
  //Serial.print("Motor speed set to : [L=");Serial.print(Lspd); Serial.print(", R=");Serial.print(Rspd);Serial.println("]");
  //answ=1; //if we receive the instruction and everything is ok, we send back answer to True (the instruction is received and performed);
}

void sendit(){
  Wire.write(ismovin);
  //answ=0; //make the answer False when it is sent.
}

void drive(int Lspd, int Rspd){
  //perform driving the motors.
  //Serial.print("The motors will drive with: [");Serial.print(Lspd); Serial.print(", ");Serial.print(Rspd);Serial.println("]");
  if (Lspd > 0){
    analogWrite(LBW, 0);
    analogWrite(LFW, Lspd);
    ismovin = 1;
    ledon=true;
  }else if(Lspd < 0){
    analogWrite(LFW, 0);
    analogWrite(LBW, -Lspd);
    ismovin = 1;
    ledon=true;
  }else{
    analogWrite(LFW, 0);
    analogWrite(LBW, 0);
    ismovin = 0;
  }
  if (Rspd > 0){
    analogWrite(RBW, 0);
    analogWrite(RFW, Rspd);
    ismovin = 1;
    ledon=true;
  }else if(Rspd < 0){
    analogWrite(RFW, 0);
    analogWrite(RBW, -Rspd);
    ismovin = 1;
    ledon=true;
  }else{
    analogWrite(RFW, 0);
    analogWrite(RBW, 0);
    ismovin = 0;
  }
}


void loop() {
  unsigned long cmillis = millis(); //current millis, counter from board start
  if (lint !=0 && ledon){
    //for the left LED:
    if (cmillis - llast >= lint){
      if (Lspd > 0){
        digitalWrite(LdB, LOW);
        //if led is ON, turn the led off, and oposit
        if (!lflag) digitalWrite(LdF, HIGH);
        else digitalWrite(LdF, LOW);
      }else{
        digitalWrite(LdF, LOW);
        if (!lflag) digitalWrite(LdB, HIGH);
        else digitalWrite(LdB, LOW);
      }
      lflag = !lflag;
      llast = cmillis;
    }
  }else{
    digitalWrite(LdF, LOW);
    digitalWrite(LdB, LOW);
    lflag = false;
  }
  if (rint !=0 && ledon){
    //for the right LED:
    if (cmillis - rlast >= rint){
      if (Rspd > 0){
        digitalWrite(RdB, LOW);
        if (!rflag) digitalWrite(RdF, HIGH);
        else digitalWrite(RdF, LOW);
      }else{
        digitalWrite(RdF, LOW);
        if (!lflag) digitalWrite(RdB, HIGH);
        else digitalWrite(RdB, LOW);
      }
      rflag = !rflag;
      rlast = cmillis;
    }
  }else{
    digitalWrite(RdF, LOW);
    digitalWrite(RdB, LOW);
    rflag = false;
  }

  if (cmillis - last_run > run_int){
    if (dur !=0){
      //Serial.print("dur = ");Serial.println(dur);
      drive(Lspd, Rspd); //say the motors to drive.
      dur = dur-1;   //decrease duration with -1 interval and continue the drive. 
      last_run = cmillis;
    }else if (ledon){
      drive(0, 0);
      ledon=false;
    }
  }
  
}
