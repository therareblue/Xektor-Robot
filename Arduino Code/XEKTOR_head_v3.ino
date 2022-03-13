//#include <Wire.h>
#include <Servo.h>
#include "Adafruit_VL53L0X.h"

Adafruit_VL53L0X lox = Adafruit_VL53L0X();

#define H_SRV1 7 //Servo for Left/Right
#define H_SRV2 8 //Servo for UP/DOWN
#define H_SRV3 4 //Servo for side move
#define H_LED_R 5 //LED Rred PWM
#define H_LED_G 6 //LED Green PWM
#define H_LED_B 9 //LED Blue PWM

Servo HSRV1;
Servo HSRV2;
Servo HSRV3;
int s1_0 = 90;  int s1_min = s1_0 - 70; int s1_max = s1_0 + 70;
int s2_0 = 95;  int s2_min = 130;
int s3_0 = 100;
int xRot = s2_0; //degree of rotation UP/down
int zRot = s3_0; // degree of rotation sideL/sideR


//COLORS ---------------
byte red[] = {255, 0, 0}; // byte is 8 bit from 0 to 255;
byte green[] = {0, 255, 0}; 
byte blue[] = {0, 0, 255};
byte cyan[] = {0, 255, 255};
byte orrange[] = {255, 100, 0};
byte yellow[] = {255, 255, 0};
byte purple[] = {255, 0, 255};

byte colr[3];
//----------------------

byte instr[] = {255, 255}; // initializing instruction to be inactive (if it is [0,0] it will perform scan
//byte instruction = 0;
byte distance, measure_count = 0;
byte ledit = 0; 
//--Timing ------
unsigned long lastLed, lastBlink, last_print = 0;
int led_counter, blink_counter = 0;
int led_int = 100;

unsigned long last_cmd = 0;
bool slept = false;

unsigned long opstart = 0;

// ==> FUNCTIONS ==============================
void smartDelay(int mSc){
  unsigned long strt = millis();
  while (millis() < strt+mSc){
    //wait in mSc
  }
}

//LED-------------------
void LEDon(byte LEDcolor[3]){
  analogWrite(H_LED_R, LEDcolor[0]);
  analogWrite(H_LED_G, LEDcolor[1]);
  analogWrite(H_LED_B, LEDcolor[2]);
}
void LEDoff(){
  analogWrite(H_LED_R, 0);
  analogWrite(H_LED_G, 0);
  analogWrite(H_LED_B, 0);
}

void eyeBlink(byte LEDcolor[3]){
  unsigned long tmstamp = millis();
  if (tmstamp - lastBlink >= led_int){
    //Serial.print("blink_counter = "); Serial.println(blink_counter);
    if (blink_counter == -2) LEDon(LEDcolor);
    if (blink_counter == -1) LEDoff();
    if (blink_counter == 0) LEDon(LEDcolor);
    if (blink_counter == 35) LEDoff();
    if (blink_counter == 36) LEDon(LEDcolor);
    if (blink_counter >= 80){
      LEDoff();
      blink_counter = -3;
    }else blink_counter++;
    lastBlink = tmstamp;
  }
}

void scanBlink(byte LEDcolor[3]){
  unsigned long tmstamp = millis();
  if (tmstamp - lastLed >= led_int){
    if (led_counter == 0){
      LEDon(LEDcolor);
      led_counter = 1;
    }
    else if (led_counter ==1){
      LEDoff();
      led_counter = 0;
    }
    else led_counter = 0;
    lastLed = tmstamp;
  }
}

void hitBlink(){
  //this function will delay the next move for total of 1 second.
  for (int i=0; i<10; i++){
    LEDon(red);
    delay(50);
    LEDoff();
    delay(50);
  }
}
//SERVO-----------------
void srvZero(){ //zeroing all servoes
  HSRV1.write(s1_0); //zeroing servoes 
  HSRV2.write(s2_0);
  HSRV3.write(s3_0);
}

void hitReaction(){
  //scanBlink(red);
  HSRV1.write(s1_0);
  HSRV3.write(s3_0-55);
  HSRV2.write(s2_0-20);
  //delay(1000);
  hitBlink(); // I have no delay above, because the hitBlink() function has a delay about 10 times by 0.1s = 1s
  HSRV3.write(s3_0);
  HSRV2.write(s2_0+20);
  for (int i=0; i<5; i++){
    scanBlink(purple);
    HSRV3.write(s3_0-50);
    //HSRV2.write(s2_0-10);
    HSRV1.write(s1_0-25);
    delay(100);
    HSRV3.write(s3_0+50);
    //HSRV2.write(s2_0+10);
    HSRV1.write(s1_0+25);
    delay(100);
  }
  LEDoff();
  HSRV3.write(s3_0);
  HSRV2.write(s2_0);
  HSRV1.write(s1_0);
  
}

void surPrise(){
  HSRV1.write(s1_0);
  HSRV3.write(s3_0-55);
  HSRV2.write(s2_0-20);
  hitBlink(); // I have no delay above, because the hitBlink() function has a delay about 10 times by 0.1s = 1s
  hitBlink();
  LEDoff();
  HSRV3.write(s3_0);
  HSRV2.write(s2_0);
  HSRV1.write(s1_0);
}

int laserMeasure(){
  int tof_mm = 0;
  //Serial.println("Scan Overlay...");
  VL53L0X_RangingMeasurementData_t measure;
  lox.rangingTest(&measure, false);
  delay(10);
  if (measure.RangeStatus != 4){
    tof_mm = measure.RangeMilliMeter-30;
    measure_count = 0;
  }
  else{
    if (measure_count >2){
      //Serial.println("Overflow");
      tof_mm = 2500;
    }else{
      measure_count++;
      tof_mm = laserMeasure();
    }
  }
  return tof_mm;
}

void receiveEvent(int howMany){
  //RULES: I CANT GO OUT OF THIS FUNCTION CALLING ANOTHER FUNCTION.
  
  int i =0;
  while (Wire.available()){
    byte c = Wire.read();
    instr[i] = c;
    i++;
  }
  Serial.print("an instruction is received:");
  Serial.print("[");Serial.print(instr[0]);Serial.print(",");Serial.print(instr[1]);Serial.println("]");
}

void sendData(){
  //byte dataByte = distance;
  //Serial.print("Data to send -> ");Serial.println(distance);
  //Serial.print("dataByte = ");Serial.print(dataByte);Serial.print(" --> distance = ");Serial.print(distance);
  Serial.println(distance);
  Wire.write(distance);
}

void setup() {
  //Serial.begin(115200);
  //delay(1000);

  //Serial.println("Setup the head LEDs...");
  //LED
  pinMode(H_LED_R, OUTPUT);
  pinMode(H_LED_G, OUTPUT);
  pinMode(H_LED_B, OUTPUT);
  delay(200);

  //Serial.println("Initializing Servoes...");
  //SERVOS
  HSRV1.attach(H_SRV1);
  delay(100); 
  HSRV2.attach(H_SRV2);
  delay(100); 
  HSRV3.attach(H_SRV3);
  delay(100); 
  srvZero();
  delay(200);

  LEDon(cyan);
  //ledit = 2;
  
  //I2C
  Wire.begin(0x06);
  delay(50);
  Wire.onReceive(receiveEvent);
  Wire.onRequest(sendData);

  delay(200);
  if (!lox.begin()) {
    distance = 254;
    //while (1);
  }
  delay(1000);
  
  //Serial.println("HEAD setup is ready!");
  last_cmd = millis();
}

void goSleep(){
  HSRV1.write(s1_0 + 30);
  HSRV3.write(s3_0);

  HSRV2.write(s2_min-30);delay(70);HSRV2.write(s2_min-25);delay(70);HSRV2.write(s2_min-20);delay(100);HSRV2.write(s2_min-15);delay(100);HSRV2.write(s2_min-10);delay(100);HSRV2.write(s2_min-5);delay(100);HSRV2.write(s2_min);
  
  LEDoff();
  ledit = 0;
  slept = true;
}

void loop() {
  switch(ledit){
    case 0:
      LEDoff();
      break;
    case 1:
      eyeBlink(blue);
      break;
    case 2:
      eyeBlink(cyan);
      break;
    case 3:
      eyeBlink(purple);
      break;
    case 4:
      scanBlink(green);
      break;
    case 5:
      scanBlink(yellow);
      break;
    case 6:
      scanBlink(red);
      break;
  }

  switch (instr[0]){
    case 0: //servo HSRV1
      { 
        ledit=0;
        last_cmd = millis();
        HSRV2.write(s2_0);
        HSRV3.write(s3_0);
        
        LEDon(green);
        //unsigned long opstart = millis();
        
        int positi[] = {-70, -35, 0, 35, 70};
        xRot = s1_0 + positi[instr[1]]; //perform rotation to desired degree value (index 0, 1, 2, 3, 4 of positi)
        //Serial.print("Instr [1] = ");Serial.println(instr[1]);
        //Serial.print("Rotating to "); Serial.println(positi[instr[1]]);
        HSRV1.write(xRot);
        delay(150);
        //smartDelay(150);
        LEDoff();
        int tof_mm = laserMeasure();
        if (tof_mm < 0) distance = 250;
        else if (tof_mm > 2200) distance = 230; 
        else distance = tof_mm / 10;

        //Serial.print("Obsticle at = ");Serial.print(distance); Serial.print(" cm. --> ");
        
        instr[0] = 255; instr[1]=255; //deactivating the instructions byte.

        //Serial.print(millis()-opstart); Serial.println(" ms");
        
      }break;
    case 1:
      { int positi[] = {-70, -35, 0, 35, 70};
        //servo zero
        ledit=0;
        last_cmd = millis();
        //Serial.print("repositioning: "); Serial.print(instr[1]);
        if (instr[1]==0) srvZero();
        else {
          xRot = s1_0 -35;
          //xRot = s1_0 + positi[instr[1]-1];
          //Serial.println(xRot);
          HSRV1.write(xRot);
          //delay(300);
        }

        instr[0] = 255; instr[1]=255; //deactivating the instructions byte.
      }break;
    
    case 2:
      {
        ledit=0;
        last_cmd = millis();
        surPrise();
        instr[0] = 255; instr[1]=255; //deactivating the instructions byte.
      }break;
    
    case 3:
      {
        ledit=0;
        last_cmd = millis();
        
        //reaction of robot impact. It only moves its head. nothing to send back;
        hitReaction();
        instr[0] = 255; instr[1]=255; //deactivating the instructions byte.
      }break;
    case 4:
      {
        last_cmd = millis();
        ledit = 3;
      }break;
  }
  
  if (millis() - last_cmd > 15000){
    if (!slept){
      instr[0] = 255; instr[1] = 255;
      goSleep();
    }
  }else slept=false;

  if (millis() - last_cmd > 1100 && !slept) {
    instr[0] = 255; instr[1] = 255;
    ledit = 2;
  }
/*
  if (millis() - last_print > 100){
    //Serial.print(millis()); Serial.print(" - "); Serial.print(last_print); Serial.print(" = "); Serial.print(millis()-last_print); Serial.print(" | -->> "); Serial.print("ledit = "); Serial.println(ledit);
    Serial.print("instr still:");
    Serial.print("[");Serial.print(instr[0]);Serial.print(",");Serial.print(instr[1]);Serial.println("]");
    last_print = millis();
    //Serial.print(millis());Serial.print(" - "); Serial.print(last_cmd);Serial.print(" = "); Serial.println(millis() - last_cmd);
  }*/
  //smartDelay(500);
}
