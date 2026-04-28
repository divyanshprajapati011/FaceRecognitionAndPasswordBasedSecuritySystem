#include <Servo.h>
#include <LiquidCrystal.h>
#include <Keypad.h>

// LCD
LiquidCrystal lcd(7, 6, 5, 4, 3, 2);

// Servo
Servo myServo;

// Pins
int ledPin = 10;
int buzzerPin = 11;

// Keypad
const byte ROWS = 4;
const byte COLS = 4;

char keys[ROWS][COLS] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

byte rowPins[ROWS] = {12, 13, A0, A1};
byte colPins[COLS] = {A2, A3, A4, A5};

Keypad keypad = Keypad(makeKeymap(keys), rowPins, colPins, ROWS, COLS);

// Variables
String enteredPassword = "";
bool passwordEntered = false;

void setup() {
  Serial.begin(9600);

  lcd.begin(16, 2);
  lcd.print("Enter Password:");

  myServo.attach(9);
  myServo.write(0);

  pinMode(ledPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
}

void loop() {

  // 🔐 Password Input
  char key = keypad.getKey();

  if (key) {
    if (key == '#') {
      Serial.println(enteredPassword); // Send to Python
      lcd.clear();
      lcd.print("Checking...");
      enteredPassword = "";
    }
    else if (key == '*') {
      enteredPassword = "";
      lcd.setCursor(0,1);
      lcd.print("                ");
    }
    else {
      enteredPassword += key;
      lcd.setCursor(0,1);
      lcd.print(enteredPassword);
    }
  }

  // 🤖 Python Commands
  if (Serial.available()) {
    char data = Serial.read();

    if (data == 'F') {
      lcd.clear();
      lcd.print("Show Face...");
    }

    else if (data == '1') {
      accessGranted();
    }

    else if (data == '0') {
      accessDenied();
    }
  }
}

void accessGranted() {
  lcd.clear();
  lcd.print("Access Granted");

  digitalWrite(ledPin, HIGH);
  tone(buzzerPin, 1000);

  myServo.write(90);
  delay(3000);

  noTone(buzzerPin);
  digitalWrite(ledPin, LOW);

  myServo.write(0);

  lcd.clear();
  lcd.print("Enter Password:");
}

void accessDenied() {
  lcd.clear();
  lcd.print("Access Denied");

  for(int i=0;i<3;i++) {
    digitalWrite(ledPin, HIGH);
    tone(buzzerPin, 500);
    delay(300);
    digitalWrite(ledPin, LOW);
    noTone(buzzerPin);
    delay(300);
  }

  lcd.clear();
  lcd.print("Enter Password:");
}