#include <Servo.h>

// Pin Definitions
#define LED_PIN 13        // Built-in LED or external LED
#define SERVO_PIN 12      // Servo motor for gate
#define BUZZER_PIN 11     // Buzzer for feedback
#define RELAY_PIN 10      // Relay for electromagnetic lock

// Servo Object
Servo gateServo;

// Timing variables
unsigned long previousMillis = 0;
const long unlockDuration = 5000;  // 5 seconds unlock time
bool gateUnlocked = false;

void setup() {
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(RELAY_PIN, OUTPUT);
  
  // Servo setup
  gateServo.attach(SERVO_PIN);
  gateServo.write(0);  // Gate closed (0 degrees)
  
  // Initial state - locked
  digitalWrite(LED_PIN, LOW);      // Red LED OFF (or connect red LED to show locked)
  digitalWrite(RELAY_PIN, HIGH);   // Relay OFF (lock engaged - assuming active LOW)
  digitalWrite(BUZZER_PIN, LOW);
  
  // Serial communication
  Serial.begin(9600);
  Serial.println("🔐 Gate Controller Ready!");
  delay(1000);
}

void loop() {
  // Check for serial data
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    Serial.println("📨 Received: " + command);
    
    if (command == "1") {
      unlockGate();
    } 
    else if (command == "0") {
      lockGate();
    }
    else if (command == "RESET") {
      resetSystem();
    }
  }
  
  // Auto-lock after unlock duration
  if (gateUnlocked && (millis() - previousMillis >= unlockDuration)) {
    lockGate();
  }
}

void unlockGate() {
  if (!gateUnlocked) {
    Serial.println("✅ GATE UNLOCKED!");
    
    // Visual feedback
    digitalWrite(LED_PIN, HIGH);     // Green LED ON
    gateServo.write(90);             // Open gate
    digitalWrite(RELAY_PIN, LOW);    // Unlock relay
    
    // Success buzzer (3 short beeps)
    successBeep();
    
    gateUnlocked = true;
    previousMillis = millis();
  }
}

void lockGate() {
  Serial.println("🔒 GATE LOCKED!");
  
  // Visual feedback
  digitalWrite(LED_PIN, LOW);      // LED OFF
  gateServo.write(0);              // Close gate
  digitalWrite(RELAY_PIN, HIGH);   // Lock relay
  
  // Lock buzzer (1 long beep)
  tone(BUZZER_PIN, 1000, 500);
  delay(600);
  
  gateUnlocked = false;
}

void successBeep() {
  // 3 short success beeps
  for (int i = 0; i < 3; i++) {
    tone(BUZZER_PIN, 2000, 100);
    delay(150);
  }
}

void resetSystem() {
  Serial.println("🔄 System Reset!");
  lockGate();
}
