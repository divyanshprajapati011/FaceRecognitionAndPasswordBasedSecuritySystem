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
