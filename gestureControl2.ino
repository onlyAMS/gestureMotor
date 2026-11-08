#include <Servo.h>

const int greenPin = 8;
const int yellowPin = 9;
const int redPin = 10;

Servo myServo;

String lastReading = "";

void setup() {
  pinMode(greenPin, OUTPUT);
  pinMode(yellowPin, OUTPUT);
  pinMode(redPin, OUTPUT);

  Serial.begin(9600);

  myServo.attach(6);
}

void loop() {
  if (Serial.available() > 0) {

    String data = Serial.readStringUntil('\n');
    data.trim();

    // Skip if the reading hasn't changed
    if (data == lastReading) {
      return;
    }

    // Update the previous reading
    lastReading = data;

    if (data == "closed_palm") {
      digitalWrite(greenPin, HIGH);
      digitalWrite(yellowPin, LOW);
      digitalWrite(redPin, LOW);
      myServo.write(90);
    }

    else if (data == "open palm") {
      digitalWrite(greenPin, LOW);
      digitalWrite(yellowPin, HIGH);
      digitalWrite(redPin, LOW);
      myServo.write(180);
    }

    else if (data == "thumbs") {
      digitalWrite(greenPin, HIGH);
      digitalWrite(yellowPin, HIGH);
      digitalWrite(redPin, HIGH);
    }

    else {
      digitalWrite(greenPin, LOW);
      digitalWrite(yellowPin, LOW);
      digitalWrite(redPin, LOW);
      myServo.write(0);
    }
  }
}