// #include <Servo.h>

// // Pin Definitions
// #define LED_PIN 13        // Built-in LED or external LED
// #define SERVO_PIN 12      // Servo motor for gate
// #define BUZZER_PIN 11     // Buzzer for feedback
// #define RELAY_PIN 10      // Relay for electromagnetic lock

// // Servo Object
// Servo gateServo;

// // Timing variables
// unsigned long previousMillis = 0;
// const long unlockDuration = 5000;  // 5 seconds unlock time
// bool gateUnlocked = false;

// void setup() {
//   // Initialize pins
//   pinMode(LED_PIN, OUTPUT);
//   pinMode(BUZZER_PIN, OUTPUT);
//   pinMode(RELAY_PIN, OUTPUT);
  
//   // Servo setup
//   gateServo.attach(SERVO_PIN);
//   gateServo.write(0);  // Gate closed (0 degrees)
  
//   // Initial state - locked
//   digitalWrite(LED_PIN, LOW);      // Red LED OFF (or connect red LED to show locked)
//   digitalWrite(RELAY_PIN, HIGH);   // Relay OFF (lock engaged - assuming active LOW)
//   digitalWrite(BUZZER_PIN, LOW);
  
//   // Serial communication
//   Serial.begin(9600);
//   Serial.println("🔐 Gate Controller Ready!");
//   delay(1000);
// }

// void loop() {
//   // Check for serial data
//   if (Serial.available() > 0) {
//     String command = Serial.readStringUntil('\n');
//     command.trim();
    
//     Serial.println("📨 Received: " + command);
    
//     if (command == "1") {
//       unlockGate();
//     } 
//     else if (command == "0") {
//       lockGate();
//     }
//     else if (command == "RESET") {
//       resetSystem();
//     }
//   }
  
//   // Auto-lock after unlock duration
//   if (gateUnlocked && (millis() - previousMillis >= unlockDuration)) {
//     lockGate();
//   }
// }

// void unlockGate() {
//   if (!gateUnlocked) {
//     Serial.println("✅ GATE UNLOCKED!");
    
//     // Visual feedback
//     digitalWrite(LED_PIN, HIGH);     // Green LED ON
//     gateServo.write(90);             // Open gate
//     digitalWrite(RELAY_PIN, LOW);    // Unlock relay
    
//     // Success buzzer (3 short beeps)
//     successBeep();
    
//     gateUnlocked = true;
//     previousMillis = millis();
//   }
// }

// void lockGate() {
//   Serial.println("🔒 GATE LOCKED!");
  
//   // Visual feedback
//   digitalWrite(LED_PIN, LOW);      // LED OFF
//   gateServo.write(0);              // Close gate
//   digitalWrite(RELAY_PIN, HIGH);   // Lock relay
  
//   // Lock buzzer (1 long beep)
//   tone(BUZZER_PIN, 1000, 500);
//   delay(600);
  
//   gateUnlocked = false;
// }

// void successBeep() {
//   // 3 short success beeps
//   for (int i = 0; i < 3; i++) {
//     tone(BUZZER_PIN, 2000, 100);
//     delay(150);
//   }
// }

// void resetSystem() {
//   Serial.println("🔄 System Reset!");
//   lockGate();
// }


#include <Servo.h>

Servo myServo;

const int servoPin = 9;
const int redLED = 7;
const int greenLED = 6;
const int buzzer = 11;

String input = "";

unsigned long openTime = 0;
bool isOpen = false;

void beepDotDot() {
  for (int i = 0; i < 2; i++) {
    digitalWrite(buzzer, HIGH);
    delay(120);
    digitalWrite(buzzer, LOW);
    delay(120);
  }
}

void beepRegular() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(buzzer, HIGH);
    delay(200);
    digitalWrite(buzzer, LOW);
    delay(200);
  }
}

void openGate() {
  digitalWrite(redLED, LOW);
  digitalWrite(greenLED, HIGH);
  beepDotDot();
  myServo.write(120);

  isOpen = true;
  openTime = millis();  // ⏱️ time store
}

void closeGate() {
  digitalWrite(redLED, HIGH);
  digitalWrite(greenLED, LOW);
  beepRegular();
  myServo.write(0);

  isOpen = false;
}

void setup() {
  Serial.begin(9600);
  myServo.attach(servoPin);
  myServo.write(0);

  pinMode(redLED, OUTPUT);
  pinMode(greenLED, OUTPUT);
  pinMode(buzzer, OUTPUT);

  closeGate();
}

void loop() {

  // 🔹 Serial input read
  while (Serial.available() > 0) {
    char c = Serial.read();

    if (c == '\n') {
      input.trim();

      if (input == "OPEN") {
        openGate();
      } else if (input == "CLOSE") {
        closeGate();
      }

      input = "";
    } else {
      input += c;
    }
  }

  // 🔹 Auto close after 5 seconds
  if (isOpen && millis() - openTime >= 5000) {
    closeGate();
  }
}
