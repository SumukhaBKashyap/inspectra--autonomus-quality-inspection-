"""
Inspectra - SG90 Servo Actuator Controller
Controls the 3 physical SG90 Servos:
- Servo 1: 4-Quadrant Inspection Platform Rotator (0°, 90°, 180°, 270°)
- Servo 2: Component Pusher from slope platform to sorting conveyor
- Servo 3: Sorting Diverter Arm (Nut bin vs Washer bin)
"""

from typing import Dict, Any
from .arduino import arduino
from ..config import config

class ServoController:
    async def rotate_to_angle(self, angle_deg: int) -> Dict[str, Any]:
        """Command Servo 1 to rotate inspection platform to specified angle (0°, 90°, 180°, 270°)."""
        return await arduino.send_command(
            "ROTATE_SERVO1",
            {"target_angle": angle_deg, "delay_ms": 500}
        )

    async def rotate_component_90(self) -> Dict[str, Any]:
        """Legacy helper: Command Servo 1 to rotate 90°."""
        return await self.rotate_to_angle(90)

    async def transfer_to_sorting_conveyor(self) -> Dict[str, Any]:
        """Command Servo 2 to push the inspected component from platform to sorting conveyor."""
        return await arduino.send_command(
            "TRANSFER_COMPONENT",
            {"push_angle": config.SERVO2_PUSH_ANGLE, "rest_angle": config.SERVO2_REST_ANGLE}
        )

    async def divert_to_nut_bin(self) -> Dict[str, Any]:
        """Command Servo 3 to swing arm towards Nut collection bin."""
        return await arduino.send_command(
            "SORT_NUT",
            {"angle": config.SERVO3_NUT_ANGLE, "hold_ms": 700}
        )

    async def divert_to_washer_bin(self) -> Dict[str, Any]:
        """Command Servo 3 to swing arm towards Washer collection bin."""
        return await arduino.send_command(
            "SORT_WASHER",
            {"angle": config.SERVO3_WASHER_ANGLE, "hold_ms": 700}
        )

    async def reset_all_servos(self) -> Dict[str, Any]:
        """Return all 3 SG90 servos to home/neutral rest positions."""
        return await arduino.send_command("RESET_SYSTEM")

servo_controller = ServoController()
