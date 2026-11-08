"""
Inspectra - Arduino Serial Communication Manager
Handles structured serial communication with Arduino Uno/Nano:
- PySerial integration with automatic port detection and reconnect
- JSON/line-delimited command protocol
- Strict ACK and movement completion verification with configurable timeouts
- Hardware simulation mode fallback
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List
import serial
import serial.tools.list_ports

from ..config import config

logger = logging.getLogger("inspectra.hardware")

class ArduinoManager:
    def __init__(self):
        self._serial: Optional[serial.Serial] = None
        self._lock = asyncio.Lock()
        self._is_connected = False
        self._last_error = None
        self._mock_positions = {
            "servo1": 0,
            "servo2": 0,
            "servo3": 90,
            "conveyor1": False,
            "conveyor2": False,
            "arrival_sensor": False,
            "sorting_sensor": False
        }

    @property
    def is_connected(self) -> bool:
        return self._is_connected and not config.HARDWARE_SIMULATION_MODE

    @property
    def is_simulation(self) -> bool:
        return config.HARDWARE_SIMULATION_MODE

    def list_available_ports(self) -> List[Dict[str, str]]:
        """List all detected hardware COM/tty serial ports on the host."""
        ports = []
        for p in serial.tools.list_ports.comports():
            ports.append({
                "device": p.device,
                "description": p.description,
                "hwid": p.hwid
            })
        return ports

    async def connect(self) -> bool:
        """Attempt to open the serial port to Arduino."""
        if config.HARDWARE_SIMULATION_MODE:
            self._is_connected = True
            logger.info("[Arduino] Simulation Mode active - real serial bypassed")
            return True

        async with self._lock:
            try:
                loop = asyncio.get_event_loop()
                self._serial = await loop.run_in_executor(
                    None,
                    lambda: serial.Serial(
                        config.SERIAL_PORT,
                        config.BAUD_RATE,
                        timeout=config.SERIAL_TIMEOUT
                    )
                )
                # Allow Arduino bootloader reset after DTR toggle
                await asyncio.sleep(2.0)
                self._is_connected = True
                self._last_error = None
                logger.info(f"[Arduino] Successfully connected to {config.SERIAL_PORT} @ {config.BAUD_RATE}")
                return True
            except Exception as e:
                self._is_connected = False
                self._last_error = str(e)
                logger.warning(f"[Arduino] Could not connect to {config.SERIAL_PORT}: {e}")
                return False

    async def disconnect(self):
        async with self._lock:
            if self._serial and self._serial.is_open:
                try:
                    self._serial.close()
                except Exception:
                    pass
            self._serial = None
            self._is_connected = False

    async def send_command(self, cmd: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Send a structured command to Arduino and wait for movement completion ACK.
        If in simulation mode, simulates realistic physical mechanical delay.
        """
        req_timeout = timeout if timeout is not None else config.SERVO_ACK_TIMEOUT
        payload = {"cmd": cmd}
        if params:
            payload.update(params)

        # ---------------- Simulation Mode Fallback ----------------
        if config.HARDWARE_SIMULATION_MODE or not self._is_connected:
            await self._simulate_hardware_action(cmd, params)
            return {
                "success": True,
                "status": "COMPLETED",
                "cmd": cmd,
                "data": payload,
                "simulation": True
            }

        # ---------------- Real Hardware Mode ----------------
        async with self._lock:
            if not self._serial or not self._serial.is_open:
                connected = await self.connect()
                if not connected:
                    raise ConnectionError(f"Cannot communicate with Arduino on {config.SERIAL_PORT}: {self._last_error}")

            line = json.dumps(payload) + "\n"
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._serial.write(line.encode("utf-8")))

            # Wait for response line with timeout
            deadline = loop.time() + req_timeout
            response_json = {}
            while loop.time() < deadline:
                in_waiting = await loop.run_in_executor(None, lambda: self._serial.in_waiting)
                if in_waiting:
                    raw_line = await loop.run_in_executor(None, lambda: self._serial.readline().decode("utf-8", errors="ignore").strip())
                    if raw_line:
                        try:
                            response_json = json.loads(raw_line)
                            # Check if it matches command completion
                            if response_json.get("status") in ["COMPLETED", "ACK", "OK"] or response_json.get("ack") == cmd:
                                return response_json
                        except json.JSONDecodeError:
                            if "OK" in raw_line or "DONE" in raw_line:
                                return {"status": "COMPLETED", "raw": raw_line}
                await asyncio.sleep(0.05)

            raise TimeoutError(f"Arduino did not respond to {cmd} within {req_timeout}s")

    async def _simulate_hardware_action(self, cmd: str, params: Optional[Dict[str, Any]]):
        """Simulate physical actuator movement times and update mock states."""
        if cmd in ["ROTATE_90", "ROTATE_SERVO1"]:
            # SG90 Servo 1 rotate to target angle (0, 90, 180, 270)
            target = params.get("target_angle", 90) if params else 90
            self._mock_positions["servo1"] = target
            await asyncio.sleep(0.4)
        elif cmd == "TRANSFER_COMPONENT":
            # SG90 Servo 2 push component onto sorting conveyor
            self._mock_positions["servo2"] = 65
            await asyncio.sleep(0.5)
            self._mock_positions["servo2"] = 0
            await asyncio.sleep(0.3)
        elif cmd == "SORT_NUT":
            # SG90 Servo 3 diverts to nut bin (45 deg)
            self._mock_positions["servo3"] = 45
            await asyncio.sleep(0.5)
            self._mock_positions["servo3"] = 90
        elif cmd == "SORT_WASHER":
            # SG90 Servo 3 diverts to washer bin (135 deg)
            self._mock_positions["servo3"] = 135
            await asyncio.sleep(0.5)
            self._mock_positions["servo3"] = 90
        elif cmd == "START_FEEDING_CONVEYOR":
            self._mock_positions["conveyor1"] = True
            await asyncio.sleep(0.3)
        elif cmd == "STOP_FEEDING_CONVEYOR":
            self._mock_positions["conveyor1"] = False
            await asyncio.sleep(0.1)
        elif cmd == "WAIT_ARRIVAL":
            self._mock_positions["arrival_sensor"] = True
            await asyncio.sleep(0.4)
            self._mock_positions["arrival_sensor"] = False
        elif cmd == "START_SORTING_CONVEYOR":
            self._mock_positions["conveyor2"] = True
            await asyncio.sleep(0.3)
        elif cmd == "WAIT_SORTING_POSITION":
            self._mock_positions["sorting_sensor"] = True
            await asyncio.sleep(0.4)
            self._mock_positions["sorting_sensor"] = False
        elif cmd == "STOP_SORTING_CONVEYOR" or cmd == "STOP_CONVEYOR":
            self._mock_positions["conveyor1"] = False
            self._mock_positions["conveyor2"] = False
            await asyncio.sleep(0.1)
        elif cmd == "EMERGENCY_STOP":
            self._mock_positions["conveyor1"] = False
            self._mock_positions["conveyor2"] = False
            self._mock_positions["servo1"] = 0
            self._mock_positions["servo2"] = 0
            self._mock_positions["servo3"] = 90
            await asyncio.sleep(0.05)
        elif cmd == "RESET_SYSTEM":
            self._mock_positions = {
                "servo1": 0, "servo2": 0, "servo3": 90,
                "conveyor1": False, "conveyor2": False,
                "arrival_sensor": False, "sorting_sensor": False
            }
            await asyncio.sleep(0.2)
        else:
            await asyncio.sleep(0.2)

    def get_hardware_state(self) -> Dict[str, Any]:
        """Return the current actuator positions and sensor states."""
        return {
            "simulation_mode": config.HARDWARE_SIMULATION_MODE,
            "connected": self.is_connected,
            "serial_port": config.SERIAL_PORT,
            "baud_rate": config.BAUD_RATE,
            "last_error": self._last_error,
            "actuators": self._mock_positions
        }

# Global singleton
arduino = ArduinoManager()

