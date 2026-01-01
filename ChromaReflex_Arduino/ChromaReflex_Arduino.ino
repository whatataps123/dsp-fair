#define POT A0
#define RED_BTN 2
#define GREEN_BTN 3
#define BLUE_BTN 4
#define LED 8

float alpha = 0.90;
float filtered = 0;
float envelope = 0;
// -------------------------------------------------
// ADJUST THIS THRESHOLD IF IT IS TOO SENSITIVE
// Higher = Harder hit required
// Lower = Softer hit required
float threshold = 80; 
// -------------------------------------------------

bool tapDetected = false;

void setup() {
  Serial.begin(9600);
  pinMode(RED_BTN, INPUT_PULLUP);
  pinMode(GREEN_BTN, INPUT_PULLUP);
  pinMode(BLUE_BTN, INPUT_PULLUP);
  pinMode(LED, OUTPUT);
  Serial.println("=== SYSTEM READY ===");
}

void loop() {
  int raw = analogRead(POT);
  // Low Pass Filter (Smooths out jitter)
  filtered = alpha * filtered + (1 - alpha) * raw;
  // Envelope Detector (Makes the signal positive and readable)
  envelope = 0.8 * envelope + 0.2 * abs(filtered);

  // --- TAP DETECTION ---
  if (envelope > threshold) {
    if (!tapDetected) {
      tapDetected = true;

      // ==========================================
      // DEBUG LOG: See exactly what triggered it
      // ==========================================
      Serial.print("[DEBUG] Hit Detected! Force: ");
      Serial.println(envelope);
      
      // Send the actual command to Python
      Serial.println("TAP"); 

      // Flash LED
      digitalWrite(LED, HIGH);
      delay(50);
      digitalWrite(LED, LOW);

      // Wait for Button Logic
      bool buttonPressed = false;
      while (!buttonPressed) {
        if (digitalRead(RED_BTN) == LOW) {
          Serial.println("RED");
          buttonPressed = true;
        }
        else if (digitalRead(GREEN_BTN) == LOW) {
          Serial.println("GREEN");
          buttonPressed = true;
        }
        else if (digitalRead(BLUE_BTN) == LOW) {
          Serial.println("BLUE");
          buttonPressed = true;
        }
        delay(10);
      }
      delay(300); // Debounce
    }
  }
  else {
    tapDetected = false;
  }
  
  delay(10);
}