/*
  LDR and Laser Fencing Security System
  
  Description:
  This sketch monitors an LDR (Light Dependent Resistor) which is being illuminated by a laser.
  When the laser beam is broken, the resistance of the LDR increases, causing the analog reading to drop.
  The Arduino detects this drop and sends an "INTRUSION" signal over the Serial port.
  
  Wiring:
  - LDR: Connect one leg to 5V, the other leg to Analog Pin A0 AND to GND via a 10k resistor (voltage divider).
  - Laser Module: Connect to 5V and GND.
  - Optional Buzzer: Connect positive leg to Digital Pin 8, negative to GND.
*/

const int ldrPin = A0;      // Analog pin connected to the LDR
const int buzzerPin = 8;    // Digital pin connected to a buzzer (optional)
const int threshold = 500;  // Threshold value; adjust based on ambient light and laser brightness

void setup() {
  Serial.begin(9600);       // Initialize Serial communication at 9600 baud rate
  pinMode(ldrPin, INPUT);
  pinMode(buzzerPin, OUTPUT);
  
  Serial.println("System Initialized. Laser Fencing Active.");
}

void loop() {
  int ldrValue = analogRead(ldrPin);
  
  // Output the raw value for debugging and dashboard monitoring
  // Format: LDR_VALUE:<value>
  Serial.print("LDR_VALUE:");
  Serial.println(ldrValue);

  // If the reading is below the threshold, the beam is broken
  if (ldrValue < threshold) {
    Serial.println("STATUS:INTRUSION");
    
    // Sound the buzzer
    digitalWrite(buzzerPin, HIGH);
    delay(1000); // Keep alarm on for 1 second
    digitalWrite(buzzerPin, LOW);
  } else {
    Serial.println("STATUS:SECURE");
  }

  // Small delay for stability
  delay(500); 
}
