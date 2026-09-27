// Streams button + joystick status over USB serial as one JSON line every 50 ms.
// status.html shows it; controller.py turns button presses into slide/volume actions.
//
// Wiring (Arduino Nano):
//   Button 1 (next / vol up)    D2   other leg -> GND (- rail)
//   Button 2 (prev / vol down)  D3   other leg -> GND (- rail)
//   Joystick VRX                A0
//   Joystick VRY                A1
//   Joystick SW                 D4
//   Joystick +5V                5V  (+ rail)
//   Joystick GND                GND (- rail)
//   Encoder CLK                 D5
//   Encoder DT                  D6
//   Encoder SW                  D7
//   Encoder +                   5V  (+ rail)
//   Encoder GND                 GND (- rail)

const int JOY_X_PIN = A0;
const int JOY_Y_PIN = A1;
const int ENC_CLK_PIN = 5;
const int ENC_DT_PIN = 6;
const int ENC_STEPS_PER_CLICK = 4;  // KY-040: 4 signal changes per detent
const unsigned long DEBOUNCE_MS = 30;

// Quadrature decoder: index = (previous AB << 2) | current AB.
// Invalid jumps (contact bounce) count as 0, so no separate debounce is needed.
const int8_t ENC_TABLE[16] = {0, -1, 1, 0, 1, 0, 0, -1, -1, 0, 0, 1, 0, 1, -1, 0};
volatile uint8_t encLast;
volatile long encSteps = 0;

// Momentary buttons, active-low. A press is counted when a button goes down.
struct Button {
  const char *key;
  int pin;
  int state;               // debounced level
  int lastRaw;
  unsigned long lastRawChange;
  unsigned long presses;
};

Button buttons[] = {
  {"b1", 2},
  {"b2", 3},
  {"sw", 4},
  {"eb", 7},  // encoder push
};
const int NUM_BUTTONS = sizeof(buttons) / sizeof(buttons[0]);

unsigned long lastSend = 0;

void setup() {
  Serial.begin(115200);
  for (Button &b : buttons) {
    pinMode(b.pin, INPUT_PULLUP);
    b.state = b.lastRaw = digitalRead(b.pin);
  }
  pinMode(ENC_CLK_PIN, INPUT_PULLUP);
  pinMode(ENC_DT_PIN, INPUT_PULLUP);
  encLast = (digitalRead(ENC_CLK_PIN) << 1) | digitalRead(ENC_DT_PIN);

  // Pin-change interrupt on D5/D6 (PCINT21/22), so no turn is missed while Serial is busy.
  PCMSK2 |= _BV(PCINT21) | _BV(PCINT22);
  PCICR |= _BV(PCIE2);
}

ISR(PCINT2_vect) {
  uint8_t ab = (digitalRead(ENC_CLK_PIN) << 1) | digitalRead(ENC_DT_PIN);
  if (ab == encLast) return;
  encSteps += ENC_TABLE[(encLast << 2) | ab];
  encLast = ab;
}

void loop() {
  // Debounce: accept a new level only after it holds for DEBOUNCE_MS.
  for (Button &b : buttons) {
    int raw = digitalRead(b.pin);
    if (raw != b.lastRaw) {
      b.lastRaw = raw;
      b.lastRawChange = millis();
    } else if (raw != b.state && millis() - b.lastRawChange >= DEBOUNCE_MS) {
      b.state = raw;
      if (raw == LOW) b.presses++;
    }
  }

  if (millis() - lastSend < 50) return;
  lastSend = millis();

  // e.g. {"b1":0,"b1n":3,...,"eb":0,"ebn":1,"enc":-7,"x":512,"y":510,"max":1023}
  // <key> is 1 while held, <key>n is the press count since power-up.
  // enc is the encoder position in clicks since power-up (clockwise = up).
  Serial.print('{');
  for (Button &b : buttons) {
    Serial.print('"'); Serial.print(b.key); Serial.print(F("\":"));
    Serial.print(b.state == LOW);
    Serial.print(F(",\"")); Serial.print(b.key); Serial.print(F("n\":"));
    Serial.print(b.presses);
    Serial.print(',');
  }
  noInterrupts();
  long steps = encSteps;
  interrupts();
  Serial.print(F("\"enc\":"));
  Serial.print(steps / ENC_STEPS_PER_CLICK);
  Serial.print(F(",\"x\":"));
  Serial.print(analogRead(JOY_X_PIN));
  Serial.print(F(",\"y\":"));
  Serial.print(analogRead(JOY_Y_PIN));
  Serial.println(F(",\"max\":1023}"));
}
