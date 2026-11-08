# Inspectra - Complete Step-by-Step Electronics Wiring Guide
*Beginner-Friendly Hardware Manual (Zero Prior Electronics Knowledge Required)*

---

## ⚠️ The 3 Golden Rules (Read This Before Touching Any Wire)

If you have never touched electronics before, remembering these **3 rules** will keep 100% of your components safe from damage:

1. **Rule 1: All Grounds (GND / Negative) Must Be Joined Together ("Common Ground")**  
   Every component (Arduino, Servos, Sensors, Power Supplies, Relays) must share a common ground reference. If the ground is not shared, electronic signals cannot complete their circuit and components will glitch or fail to respond.
2. **Rule 2: Never Power Servos Directly from the Arduino's 5V Pin**  
   The Arduino 5V pin can only safely supply about $200\text{ mA}$ of current. Each SG90 micro servo draws up to $600\text{ mA}$ when moving. Attempting to power 3 servos from the Arduino will crash the board, restart your USB connection, or permanently burn the Arduino's internal regulator.  
   *(We will use a dedicated 5V power converter for the servos).*
3. **Rule 3: Always Double-Check Red (+) and Black/Brown (-)**  
   - **RED** is almost always Power Positive ($+5\text{V}$ or $+12\text{V}$).
   - **BLACK** or **BROWN** is Ground ($0\text{V}$ / $\text{GND}$).  
   *Swapping these two will destroy a chip in less than 1 second.*

---

## 1. Visual Component Pin Identification

### A. Arduino Uno / Nano Pin Layout
```
                          +-------------------------+
                          |       ARDUINO UNO       |
                          |                         |
                          |                   [D13] | --- Built-in LED
                          |                   [D12] | 
                          | ~PWM              [D11] | --- Servo 3 (Diverter Arm)
                          | ~PWM              [D10] | --- Servo 2 (Platform Pusher)
                          | ~PWM               [D9] | --- Servo 1 (Platform Rotator)
                          |                    [D8] | 
                          |                    [D7] | 
                          | ~PWM               [D6] | --- Conveyor 2 Relay (Sorting)
                          | ~PWM               [D5] | --- Conveyor 1 Relay (Feeding)
                          |                    [D4] | --- Emergency Stop Button
       RESET ------------ | [RESET]            [D3] | --- IR Sorting Sensor
        3.3V ------------ | [3.3V]             [D2] | --- IR Arrival Sensor
          5V ------------ | [5V]               [D1] | --- TX (Leave free)
         GND ------------ | [GND]              [D0] | --- RX (Leave free)
         GND ------------ | [GND]                   |
         VIN ------------ | [VIN]                   |
                          +-------------------------+
```

---

### B. SG90 Micro Servo (3 Wires)
Every standard SG90 servo has a 3-wire ribbon cable with a black female socket:
```
           +-------------+
           |  SG90 MOTOR |
           +------+------+
                  | 
                  |  [BROWN]  -----> GROUND (GND) -> Connect to External 5V (-)
                  |  [RED]    -----> POWER (+5V)  -> Connect to External 5V (+)
                  |  [ORANGE] -----> SIGNAL (PWM) -> Connect to Arduino Digital Pin
```
- **Servo 1 (Rotator)**: Orange wire $\rightarrow$ Arduino **Pin D9**
- **Servo 2 (Pusher)**: Orange wire $\rightarrow$ Arduino **Pin D10**
- **Servo 3 (Diverter)**: Orange wire $\rightarrow$ Arduino **Pin D11**

---

### C. 3-Pin IR Obstacle / Arrival Sensor (LM393 / TCRT5000)
```
         +----------------------------------+
         | [LEDs: IR Transmitter + Receiver]|
         |                                  |
         |  [POTENTIOMETER] (Sensitivity)   |
         |                                  |
         |   [VCC]  -----> +5V (Arduino 5V pin)
         |   [GND]  -----> GND (Arduino GND)
         |   [OUT]  -----> Digital Pin (D2 or D3)
         +----------------------------------+
```
- **Arrival Sensor (Platform)**: `OUT` pin $\rightarrow$ Arduino **Pin D2**
- **Sorting Sensor (Gate)**: `OUT` pin $\rightarrow$ Arduino **Pin D3**

---

### D. 2-Channel 5V Relay Module (For 12V Conveyor Motors)
```
      CONTROL SIDE (Low Voltage)           SWITCH SIDE (High Voltage)
      +------------------------+           +--------------------------+
      | [VCC] --> Arduino 5V   |           | [NO1]  [COM1]  [NC1]     | -> Conveyor 1 Motor
      | [IN1] --> Arduino D5   |           |                          |
      | [IN2] --> Arduino D6   |           | [NO2]  [COM2]  [NC2]     | -> Conveyor 2 Motor
      | [GND] --> Arduino GND  |           +--------------------------+
      +------------------------+
```

---

### E. LM2596 DC-DC Step-Down Buck Converter
Takes 12V from your main power supply and steps it down safely to **5.0V** for the 3 servos.
```
           INPUT SIDE                                OUTPUT SIDE
         (From 12V PSU)                            (To Servos Only!)
        +--------------+                          +----------------+
        | [IN +] (12V) |      [BRASS SCREW]       | [OUT +] (+5V)  | -> Servos Red Wires
        |              |  (Turn to calibrate 5V)  |                |
        | [IN -] (GND) |                          | [OUT -] (GND)  | -> Servos Brown Wires + Arduino GND
        +--------------+                          +----------------+
```

---

## 2. Step-by-Step Wiring Sequence

Follow these 7 steps in exact order:

### STEP 1: Calibrate the 5V Step-Down Converter (LM2596)
> [!IMPORTANT]
> **Do this BEFORE connecting the servos!**
1. Take your 12V / 5A power supply.
2. Connect the **12V Positive (+)** wire to the `IN+` screw terminal of the LM2596.
3. Connect the **12V Negative (-)** wire to the `IN-` screw terminal of the LM2596.
4. Plug in the 12V power supply. The small LED on the LM2596 will turn on.
5. Take a digital multimeter set to DC Voltage ($20\text{V}$ range).
6. Place the Red probe on `OUT+` and Black probe on `OUT-`.
7. Using a small flathead screwdriver, **rotate the tiny brass screw** on the blue potentiometer counter-clockwise until the meter reads **exactly 5.0V** (between 4.95V and 5.10V).
8. Unplug the 12V power supply. Your 5V servo supply is now calibrated and safe!

---

### STEP 2: Breadboard Power & Ground Rails Setup
A standard half-size or full-size breadboard has two long columns along each edge labeled with **+ (Red)** and **- (Blue)** lines.
```
     EXTERNAL 5V BUCK CONVERTER                    BREADBOARD RAILS
    +--------------------------+                   +--------------------+
    | OUT + (5.0V Regulated)   | ================= | (+) RED BUS RAIL   |
    | OUT - (GND Reference)    | ================= | (-) BLUE BUS RAIL  |
    +--------------------------+                   +---------+----------+
                                                             |
    ARDUINO UNO                                              | COMMON GROUND JUMPER
    +--------------------------+                             |
    | GND Pin (any GND on board)| ===========================+
    +--------------------------+
```
1. Run a jumper wire from LM2596 `OUT+` to the Breadboard **Red (+) Rail**.
2. Run a jumper wire from LM2596 `OUT-` to the Breadboard **Blue (-) Rail**.
3. Run a jumper wire from the **Arduino GND pin** to the Breadboard **Blue (-) Rail**.  
   *(This creates the Common Ground reference between Arduino and Servos).*

---

### STEP 3: Connecting the 3 SG90 Micro Servos
Now connect each servo's 3 wires:

| Servo Unit | Brown Wire (Ground) | Red Wire (Power) | Orange Wire (Signal) |
| :--- | :--- | :--- | :--- |
| **Servo 1** (Platform 90° Rotator) | Breadboard **Blue (-) Rail** | Breadboard **Red (+) Rail** | Arduino **Pin D9** |
| **Servo 2** (Component Pusher) | Breadboard **Blue (-) Rail** | Breadboard **Red (+) Rail** | Arduino **Pin D10** |
| **Servo 3** (Diverter Arm) | Breadboard **Blue (-) Rail** | Breadboard **Red (+) Rail** | Arduino **Pin D11** |

---

### STEP 4: Connecting the 2-Channel Relay Module (Conveyors)

#### A. Relay Module Low-Voltage Logic (To Arduino)
| Relay Pin | Connects To | Wire Color Recommendation |
| :--- | :--- | :--- |
| **VCC** | Arduino **5V Pin** | Red |
| **GND** | Arduino **GND Pin** | Black |
| **IN1** (Controls Conveyor 1 Feeding) | Arduino **Pin D5** | Green / Yellow |
| **IN2** (Controls Conveyor 2 Sorting) | Arduino **Pin D6** | White / Blue |

#### B. Relay Screw Terminals (Motor Circuit - Acts like a light switch)
The relay does not create power; it simply breaks and completes the $+12\text{V}$ wire going to the motor.
```
  [12V PSU (+)] -----------------------------------------> [COM1 Terminal]
                                                           [NO1 Terminal] ----> [Motor 1 (+)]
  [12V PSU (-)] --------------------------------------------------------------> [Motor 1 (-)]
```
1. Run a wire from **12V PSU (+)** to the `COM1` (Common) terminal of Relay 1.
2. Run a wire from `NO1` (Normally Open) of Relay 1 to the **Conveyor 1 Motor (+)**.
3. Connect **Conveyor 1 Motor (-)** directly to **12V PSU (-)**.
4. Repeat the exact same setup for Conveyor 2 using `COM2`, `NO2`, and **Arduino Pin D6**.

---

### STEP 5: Connecting the 2 IR Optical Sensors

#### A. Arrival Sensor (Platform Center Detection)
- `VCC` $\rightarrow$ Arduino **5V Pin** (or breadboard powered from Arduino 5V)
- `GND` $\rightarrow$ Arduino **GND Pin**
- `OUT` / `DO` $\rightarrow$ Arduino **Pin D2**

#### B. Sorting Position Sensor (Conveyor 2 Diverter Gate)
- `VCC` $\rightarrow$ Arduino **5V Pin**
- `GND` $\rightarrow$ Arduino **GND Pin**
- `OUT` / `DO` $\rightarrow$ Arduino **Pin D3**

*(Each sensor has a small blue potentiometer: place a nut under the sensor and turn the potentiometer until the sensor's second LED lights up when an object is present, and turns off when the object is removed).*

---

### STEP 6: Emergency Stop Button & Status LED
- **E-Stop Button**:
  - Connect one terminal of the push button to Arduino **Pin D4**.
  - Connect the other terminal of the push button to Arduino **GND**.  
    *(The Arduino software activates an internal pull-up resistor. When pressed, pin D4 connects to GND and triggers the immediate halt).*
- **Status LED**:
  - Arduino has a built-in LED permanently linked to **Pin D13**. No external wiring is strictly required!

---

### STEP 7: Smartphone Camera & Stand Setup
1. Mount your Android phone on a sturdy arm or 3D-printed bracket angled at **$45^\circ$** pointing down at the rotating platform.
2. Connect the phone to your local Wi-Fi.
3. Open the **IP Webcam** app on your phone, scroll to the bottom, and tap **"Start server"**.
4. The phone screen will display an address (e.g., `http://192.168.1.100:8080`).
5. Open the Inspectra web app $\rightarrow$ Settings $\rightarrow$ set camera source to your phone's address.

---

## 3. Master Connection Quick Reference Table

| Device | Component Pin | Arduino / Power Connection | Function |
| :--- | :---: | :---: | :--- |
| **Arrival Sensor** | OUT | **Pin D2** | Triggers when component lands from slope |
| **Arrival Sensor** | VCC / GND | **5V / GND** (Arduino) | Sensor power |
| **Sorting Sensor** | OUT | **Pin D3** | Triggers when component reaches diverter gate |
| **Sorting Sensor** | VCC / GND | **5V / GND** (Arduino) | Sensor power |
| **E-Stop Button** | Terminal 1 & 2 | **Pin D4 & GND** | Instantaneous hardware shutdown |
| **Relay Module** | IN1 | **Pin D5** | Controls Conveyor 1 (Feeding) |
| **Relay Module** | IN2 | **Pin D6** | Controls Conveyor 2 (Sorting) |
| **Relay Module** | VCC / GND | **5V / GND** (Arduino) | Relay logic coils |
| **Servo 1** (Rotator) | Orange (PWM) | **Pin D9** | 0° $\rightarrow$ 90° $\rightarrow$ 180° $\rightarrow$ 270° Platform sweep |
| **Servo 1** (Rotator) | Red / Brown | **Ext 5V (+) / Ext GND (-)** | High-current power from LM2596 |
| **Servo 2** (Pusher) | Orange (PWM) | **Pin D10** | Sweeps component from platform to conveyor |
| **Servo 2** (Pusher) | Red / Brown | **Ext 5V (+) / Ext GND (-)** | High-current power from LM2596 |
| **Servo 3** (Diverter) | Orange (PWM) | **Pin D11** | Deflects to Nut (45°) or Washer (135°) bin |
| **Servo 3** (Diverter) | Red / Brown | **Ext 5V (+) / Ext GND (-)** | High-current power from LM2596 |
| **Common Ground** | Blue (-) Rail | **Arduino GND Pin** | Unifies voltage reference across system |

---

## 4. Pre-Power Smoke Test Checklist

Before plugging your 12V adapter into the wall:

- [ ] **Check 1**: Did you connect external 5V to the Arduino 5V pin by accident? *(Never do this. The external 5V goes ONLY to the servos Red wires).*
- [ ] **Check 2**: Is the Arduino GND connected with a wire to the external LM2596 GND? *(Yes, must be connected).*
- [ ] **Check 3**: Are all 3 servo brown wires in the negative (-) rail and red wires in the positive (+) rail?
- [ ] **Check 4**: Did you pre-set the LM2596 screw to $5.0\text{V}$ with a multimeter before plugging in the servos?
- [ ] **Check 5**: Plug Arduino USB cable into PC first. The green `ON` light should turn on steadily.
- [ ] **Check 6**: Plug in the 12V adapter. The relay LEDs and sensor power LEDs should light up with no heat or smell.

---

## 5. Troubleshooting Common Beginner Issues

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **Servo vibrates, twitches, or doesn't move** | Missing common ground or insufficient current. | Ensure Arduino GND is firmly plugged into the Breadboard Blue (-) rail. Verify the 5V buck converter is outputting at least 4.9V. |
| **Arduino restarts/disconnects from PC when servo moves** | Servos are wired to the Arduino 5V pin instead of the external 5V supply. | Move all servo RED wires to the LM2596 $5\text{V}$ rail. |
| **IR sensor LED stays ON constantly** | Potentiometer sensitivity is set too high or background reflection. | Use a small screwdriver to turn the blue potentiometer clockwise/counter-clockwise until the light turns off in ambient room lighting. |
| **Conveyor motor doesn't spin when relay clicks** | Motor circuit is missing complete loop. | Check that 12V PSU (+) goes to `COM`, `NO` goes to Motor (+), and Motor (-) goes back to 12V PSU (-). |

