#include <bluefruit.h>

BLEDis bledis;
BLEHidGamepad gamepad;

// --- PIN DEFINITIONS ---
const int rightStickPin = A3; 
const int leftStickPin  = A5; 

// Encoder Pins
const int pinDT  = 6;
const int pinCLK = 9;
const int pinSW  = A2;

// --- VARIABLES ---
// "volatile" tells the computer this number changes in the background!
volatile int headPosition = 0;      
volatile int lastEncoded = 0; // Helps track the previous pattern

void setup() {
  Serial.begin(115200);
  
  // 1. Setup Pins with Pullups
  pinMode(pinDT, INPUT_PULLUP);
  pinMode(pinCLK, INPUT_PULLUP);
  pinMode(pinSW, INPUT_PULLUP); 

  // 2. THE INTERRUPT
  // Whenever the CLK pin voltage changes, run the 'updateEncoder' function immediately.
  attachInterrupt(digitalPinToInterrupt(pinCLK), updateEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(pinDT), updateEncoder, CHANGE);

  // 3. Setup Bluetooth
  Bluefruit.begin();
  Bluefruit.setName("Joystick Controller");
  
  bledis.setManufacturer("Adafruit");
  bledis.setModel("Feather nRF52840");
  bledis.begin();

  gamepad.begin();

  Bluefruit.Advertising.addFlags(BLE_GAP_ADV_FLAGS_LE_ONLY_GENERAL_DISC_MODE);
  Bluefruit.Advertising.addTxPower();
  Bluefruit.Advertising.addService(gamepad);
  Bluefruit.Advertising.addName();
  Bluefruit.Advertising.restartOnDisconnect(true);
  Bluefruit.Advertising.start(0);
  
  Serial.println("Controller Started! Interrupt Mode Active.");
}

// --- THIS FUNCTION RUNS IN THE BACKGROUND ---
// It runs automatically whenever the knob moves, no matter what.
void updateEncoder() {
  int MSB = digitalRead(pinDT); // Most Significant Bit
  int LSB = digitalRead(pinCLK); // Least Significant Bit

  int encoded = (MSB << 1) | LSB; // Combine the two signals
  int sum  = (lastEncoded << 2) | encoded; // Check against previous state

  // This logic matrix handles the direction perfectly
  if(sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011) headPosition += 1;
  if(sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000) headPosition -= 1;

  lastEncoded = encoded; // Save state for next time
  
  // Hard Limits
  if (headPosition > 127) headPosition = 127;
  if (headPosition < -127) headPosition = -127;
}

void loop() {
  // --- SEND BLUETOOTH DATA ---
  if (Bluefruit.connected()) {
    
    int rawRight = analogRead(rightStickPin);
    int rawLeft  = analogRead(leftStickPin);
    int8_t joyX = map(rawRight, 0, 4095, -127, 127);
    int8_t joyY = map(rawLeft,  0, 4095, -127, 127);
    
    // Read Button
    uint32_t buttonBits = 0;
    if (digitalRead(pinSW) == LOW) {
      buttonBits = 1;
      Serial.println("Beep! (Button Pressed)");
    }

    // Create Report
    hid_gamepad_report_t gp;
    gp.x       = joyX;
    gp.y       = joyY;
    gp.z       = 0;
    gp.rz      = 0;
    gp.rx      = (int8_t)headPosition; // This variable updates automatically now
    gp.ry      = 0;
    gp.hat     = 0;
    gp.buttons = buttonBits; 

    gamepad.report(&gp);
    
    // Debug Print (So we can see if it works)
    Serial.print("Right Stick: "); Serial.print(joyX);
    Serial.print(" | Left Stick: "); Serial.print(joyY);
    Serial.print(" | Head: "); Serial.println(headPosition); 

    delay(20); // Longer delay is fine now because Interrupts handle the knob!
  }
}