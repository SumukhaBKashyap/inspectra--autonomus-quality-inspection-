/*
  =============================================================================
  INSPECTRA - Ultra-Smooth Precision Inspection (Slow Speed Motion)
  =============================================================================
  
  Controls:
  - Servo 1 (Pin 9)  : Platform Rotator (Smooth degree-by-degree rotation)
  - Servo 2 (Pin 10) : Laser Profilometer (Slow, cinematic 0° -> 180° sweep)
  - IR Sensor (Pin 2): Triggers on washer arrival (Active LOW)
  - LED Strip (Pin 12): Illumination ON during scan
  - Built-in (Pin 13): Cycle Status LED

  All motions are graduated (1° per step) to eliminate jerking, vibrations,
  and washer displacement.
  =============================================================================
*/

#include <Servo.h>

const int PIN_IR_SENSOR    = 2;   // IR Arrival Sensor
const int PIN_SERVO_PLAT   = 9;   // Platform Rotator Servo (Pin 9)
const int PIN_SERVO_LASER  = 10;  // Laser Scanner Servo (Pin 10)
const int PIN_LED_STRIP    = 12;  // LED Strip Control (Pin 12)
const int PIN_STATUS_LED   = 13;  // Arduino Built-in LED

// Motion Speed Settings (Higher delay = Slower & Smoother)
const int PLATFORM_STEP_DELAY = 25; // 25ms per degree = ~2.25 seconds for 90° rotation
const int LASER_SWEEP_DELAY   = 28; // 28ms per degree = ~5.0 seconds for full 180° scan
const int LASER_RETURN_DELAY  = 15; // Return stroke speed

Servo platformServo;
Servo laserServo;

int currentPlatformAngle = 0;

// Function to smoothly rotate platform degree-by-degree (no jerking)
void rotatePlatformTo(int targetAngle) {
  Serial.print("    [PLATFORM] Smoothly rotating ");
  Serial.print(currentPlatformAngle);
  Serial.print("° -> ");
  Serial.print(targetAngle);
  Serial.println("°...");

  if (targetAngle > currentPlatformAngle) {
    for (int a = currentPlatformAngle; a <= targetAngle; a++) {
      platformServo.write(a);
      delay(PLATFORM_STEP_DELAY);
    }
  } else if (targetAngle < currentPlatformAngle) {
    for (int a = currentPlatformAngle; a >= targetAngle; a--) {
      platformServo.write(a);
      delay(PLATFORM_STEP_DELAY);
    }
  }
  currentPlatformAngle = targetAngle;
}

// Function to smoothly sweep laser profilometer 0° -> 180° -> 0°
void sweepLaserScanSlow() {
  Serial.println("    [LASER SCAN] Slow scan across surface (0° -> 180°)...");
  
  // Slow forward scan (1° per step for maximum triangulation capture)
  for (int angle = 0; angle <= 180; angle += 1) {
    laserServo.write(angle);
    delay(LASER_SWEEP_DELAY);
  }
  
  delay(300); // Settle at 180°

  Serial.println("    [LASER SCAN] Returning laser to home (180° -> 0°)...");
  // Smooth return stroke
  for (int angle = 180; angle >= 0; angle -= 2) {
    laserServo.write(angle);
    delay(LASER_RETURN_DELAY);
  }
  delay(200);
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_IR_SENSOR, INPUT);
  pinMode(PIN_LED_STRIP, OUTPUT);
  pinMode(PIN_STATUS_LED, OUTPUT);

  digitalWrite(PIN_LED_STRIP, LOW);
  digitalWrite(PIN_STATUS_LED, LOW);

  platformServo.attach(PIN_SERVO_PLAT);
  laserServo.attach(PIN_SERVO_LASER);

  // Initialize both servos smoothly to 0°
  platformServo.write(0);
  laserServo.write(0);
  currentPlatformAngle = 0;

  delay(600);
  Serial.println("==================================================================");
  Serial.println("  INSPECTRA: Ultra-Smooth Slow-Motion Inspection Ready            ");
  Serial.println("  Speed tuned: No jerking, stable camera & laser exposure         ");
  Serial.println("  Place a component near IR Sensor to start...                    ");
  Serial.println("==================================================================");
}

void loop() {
  // Check if component is detected
  if (digitalRead(PIN_IR_SENSOR) == LOW) {
    digitalWrite(PIN_STATUS_LED, HIGH);
    digitalWrite(PIN_LED_STRIP, HIGH);
    Serial.println("\n[TRIGGER] Component detected! Starting 4-Quadrant slow-motion scan:");
    delay(400);

    // ==========================================
    // QUADRANT 1: 0°
    // ==========================================
    Serial.println("\n>>> [Station 1/4] Platform Angle: 0°");
    rotatePlatformTo(0);
    delay(600);           // Settle for camera exposure
    sweepLaserScanSlow(); // Slow laser profilometry sweep
    delay(800);

    // ==========================================
    // QUADRANT 2: 90°
    // ==========================================
    Serial.println("\n>>> [Station 2/4] Platform Rotating to 90°...");
    rotatePlatformTo(90);
    delay(600);           // Settle for camera exposure
    sweepLaserScanSlow(); // Slow laser profilometry sweep
    delay(800);

    // ==========================================
    // QUADRANT 3: 180°
    // ==========================================
    Serial.println("\n>>> [Station 3/4] Platform Rotating to 180°...");
    rotatePlatformTo(180);
    delay(600);           // Settle for camera exposure
    sweepLaserScanSlow(); // Slow laser profilometry sweep
    delay(800);

    // ==========================================
    // QUADRANT 4: 90° (representing 270°)
    // ==========================================
    Serial.println("\n>>> [Station 4/4] Platform Rotating to Position 4 (90°)...");
    rotatePlatformTo(90);
    delay(600);           // Settle for camera exposure
    sweepLaserScanSlow(); // Slow laser profilometry sweep
    delay(800);

    // ==========================================
    // CYCLE COMPLETE: RETURN HOME
    // ==========================================
    Serial.println("\n[COMPLETE] 4-Quadrant multi-angle scan finished!");
    rotatePlatformTo(0);
    laserServo.write(0);

    digitalWrite(PIN_STATUS_LED, LOW);
    digitalWrite(PIN_LED_STRIP, LOW);

    // Cooldown before next inspection
    Serial.println("Cycle complete. Ready for next component in 3 seconds...\n");
    delay(3000);
  }

  delay(25);
}
