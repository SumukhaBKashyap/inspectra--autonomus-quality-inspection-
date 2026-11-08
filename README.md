# INSPECTRA — Automated Quality Inspection and Sorting System

**Inspectra** is an automated quality inspection and sorting system combining mechanical automation, multi-angle computer vision, triangular laser profilometry, simulated eddy-current analysis, and a central intelligent decision engine.

---

## 1. System Architecture

```
inspectra/
├── backend/
│   ├── vision/                     # Method 1: Computer Vision (REAL)
│   │   ├── camera.py               # Android IP Webcam / USB camera / Fallback stream
│   │   ├── preprocessing.py        # Otsu thresholding, CLAHE, morphological cleanup
│   │   ├── component_detection.py  # Contour geometry, circularity, vertices (Nut vs Washer)
│   │   ├── dimension_measurement.py# Calibrated mm/px outer/inner/flats measurements
│   │   ├── defect_detection.py     # Cracks, scratches, burrs, discoloration
│   │   └── multi_angle.py          # Combined 0° and 90° multi-view evaluation
│   ├── laser/                      # Method 2: Triangular Laser (REAL)
│   │   ├── laser_capture.py        # Frame grabber for red laser line
│   │   ├── laser_profile.py        # Sub-pixel intensity-weighted line centroid extraction
│   │   └── triangulation.py        # Height conversion Δrow*pitch/tan(θ) & warp analysis
│   ├── sensors/                    # Method 3: Eddy Current Array (SIMULATED)
│   │   └── coil_simulator.py       # 8-coil perimeter array impedance scan [SIMULATED]
│   ├── classification/             # Intelligent Decision Engine
│   │   ├── quality_classifier.py   # Independent method threshold evaluations
│   │   └── decision_engine.py      # Fused PASS / FAIL / REVIEW logic & sorting commands
│   ├── hardware/                   # Mechanical & Microcontroller Interface
│   │   ├── arduino.py              # PySerial command/ACK protocol & simulation fallback
│   │   ├── servo_controller.py     # Control for 3x SG90 servos
│   │   └── conveyor_controller.py  # Stage 1 Feeding & Stage 3 Sorting conveyors
│   ├── inspection/                 # 18-Step Workflow Sequence
│   │   └── inspection_manager.py   # State machine orchestrator & WebSocket broadcaster
│   ├── database/                   # SQLite Persistence
│   │   ├── db.py                   # Engine & session management
│   │   ├── models.py               # Inspection, Image, Results, Decision models
│   │   └── crud.py                 # Historical records, filters & KPI aggregations
│   ├── api/                        # REST & Streaming Endpoints
│   │   ├── routes_inspection.py    # Trigger, inspect, filter, stats, export CSV/JSON
│   │   ├── routes_hardware.py      # Direct servo/conveyor actuators & E-Stop
│   │   ├── routes_settings.py      # Configuration & tolerances
│   │   ├── routes_stream.py        # Live MJPEG video feed
│   │   └── websocket_hub.py        # Live inspection WebSocket pub/sub
│   ├── config.py                   # Runtime configuration & persistent settings
│   ├── main.py                     # FastAPI application entrypoint
│   └── run.py                      # Startup script
│
├── frontend/                       # Modern Industrial Dark Theme Dashboard
│   ├── src/
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx       # KPI metrics, throughput, quality charts
│   │   │   ├── LiveInspectionPage.tsx  # MJPEG camera, 0°/90° views, 3 method outputs
│   │   │   ├── SortingMonitorPage.tsx  # Stage schematic, servo gauges, E-Stop
│   │   │   ├── InspectionHistoryPage.tsx# Filterable records & telemetry inspector
│   │   │   ├── ReportsPage.tsx         # SPC statistics, defect Pareto, export
│   │   │   └── SettingsPage.tsx        # Camera URLs, COM port, tolerances, calibration
│   │   ├── services/
│   │   │   └── api.ts                  # REST API & WebSocket service
│   │   ├── App.tsx                     # Navigation header & tab switcher
│   │   └── index.css                   # Tailwind CSS styling & industrial glows
│   ├── package.json
│   └── vite.config.ts
│
├── arduino/
│   └── inspectra_controller.ino     # Firmware for Arduino Uno/Nano (Servos + Conveyors)
│
└── dataset/
    ├── generate_samples.py         # Synthetic sample generator
    ├── nuts/                       # 0° and 90° nut samples
    ├── washers/                    # 0° and 90° washer samples
    ├── pass/                       # Passing reference samples
    ├── fail/                       # Defective samples (scratches, burrs)
    └── laser/                      # Baseline and height profile sample frames
```

---

## 2. Three Quality Inspection Methods

1. **Method 1: Computer Vision (REAL)**
   - Smartphone camera at 45°–60° captures initial stationary image (0°).
   - SG90 Servo 1 rotates component by 90°.
   - Camera captures rotated image (90°).
   - Component identified as **NUT** or **WASHER** using circularity ($4\pi A / P^2$) and polygon vertex approximations.
   - Measures across-flats width, outer diameter, and inner hole diameter in millimetres using calibrated scaling factor (`CV_MM_PER_PIXEL`).
   - Detects perimeter burrs and surface cracks via high-pass Laplacian filtering.

2. **Method 2: Triangular Laser Inspection (REAL)**
   - Red laser line is projected across the component.
   - Intensity-weighted column centroid algorithm extracts sub-pixel laser stripe positions.
   - Triangulation formula converts pixel displacement into calibrated height profile (mm):
     $$\text{Height} = \frac{\Delta\text{row} \times \text{pixel\_pitch}}{\tan(\theta)}$$
   - Computes surface flatness across component face, peak-to-valley variance ($\Delta h$), and roughness ($\sigma$).

3. **Method 3: Eddy Current Array (SIMULATED)**
   - Simulates multi-coil impedance inspection around the component perimeter.
   - Injects subsurface defect spikes outside nominal baseline ($\pm 12\%$).
   - ⚠️ **Notice:** This method is simulated. Every metric and chart is labeled **`[SIMULATED]`**.

---

## 3. Intelligent Decision Engine & Mechanical Sorting

| Quality Status | Component Type | Decision Action | Conveyor Mechanism |
| :--- | :--- | :--- | :--- |
| **PASS** | NUT | `SORT_NUT` | Servo 2 transfers to conveyor; Servo 3 diverts to **Nut Bin** (45°) |
| **PASS** | WASHER | `SORT_WASHER` | Servo 2 transfers to conveyor; Servo 3 diverts to **Washer Bin** (135°) |
| **FAIL** | Any | `STOP_CONVEYOR` | Both conveyors stop immediately for **Manual Removal** |
| **REVIEW** | Any | `STOP_CONVEYOR` | Conveyor stops immediately for **Manual Inspection** |
| **UNKNOWN**| UNKNOWN | `STOP_CONVEYOR` | Conveyor stops immediately for **Manual Identification** |

---

## 4. Hardware Wiring & Pinout (Arduino Uno / Nano)

> [!WARNING]
> **CRITICAL POWER REQUIREMENT:**
> SG90 micro servos draw up to 600mA stall current each. **Never power servos from the Arduino 5V pin.**
> Use an external regulated **5V / 2A+ power supply** with a **common ground (GND)** connected to the Arduino GND.

| Component | Pin | Function |
| :--- | :--- | :--- |
| **Optical Arrival Sensor** | Digital Pin 2 | Active LOW when component reaches Stage 2 platform |
| **Optical Sorting Sensor** | Digital Pin 3 | Active LOW when component reaches Servo 3 diverter |
| **Emergency Stop Button** | Digital Pin 4 | Active LOW with internal pull-up |
| **Feeding Conveyor Motor** | Digital Pin 5 | Stage 1 feeding conveyor relay/driver |
| **Sorting Conveyor Motor** | Digital Pin 6 | Stage 3 sorting conveyor relay/driver |
| **SG90 Servo 1** | Digital Pin 9 | 90° component rotator on inspection platform |
| **SG90 Servo 2** | Digital Pin 10 | Pusher from platform onto sorting conveyor |
| **SG90 Servo 3** | Digital Pin 11 | Swinging diverter arm (Nut: 45°, Washer: 135°, Neutral: 90°) |

---

## 5. Quick Start Instructions

### Prerequisites
- Python 3.10+ (with `fastapi`, `uvicorn`, `opencv-python`, `numpy`, `sqlalchemy`, `pyserial`)
- Node.js 18+ and npm

### 1. Launch Backend Service
```bash
cd backend
python run.py
```
- API starts at `http://localhost:8000`
- Interactive Swagger docs: `http://localhost:8000/docs`
- Live MJPEG stream: `http://localhost:8000/api/stream/video_feed`

### 2. Launch Frontend Industrial Dashboard
```bash
cd frontend
npm run dev
```
- Dashboard opens at `http://localhost:5173`

### 3. Hardware Simulation vs Real Hardware Mode
- To run with physical hardware connected: Open **Settings** tab in the dashboard, toggle **Hardware Simulation Mode** OFF, select your Arduino COM port, and click **Save Changes**.
- When Arduino is not physically connected: Leave **Hardware Simulation Mode** ON. All 18 workflow steps, servo kinematics, sensor triggers, and inspection algorithms will simulate accurately.
#   i n s p e c t r a - - a u t o n o m u s - q u a l i t y - i n s p e c t i o n -  
 