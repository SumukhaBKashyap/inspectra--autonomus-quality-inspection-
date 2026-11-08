"""
Inspectra - Conveyor Motor and Sensor Controller
Controls:
- Stage 1: Feeding conveyor motor
- Stage 3: Transfer & sorting conveyor motor
- Optical arrival sensor and sorting sensor inputs
- Emergency stop circuit
"""

from typing import Dict, Any
from .arduino import arduino

class ConveyorController:
    async def start_feeding_conveyor(self) -> Dict[str, Any]:
        """Start Stage 1 feeding conveyor."""
        return await arduino.send_command("START_FEEDING_CONVEYOR")

    async def stop_feeding_conveyor(self) -> Dict[str, Any]:
        """Stop Stage 1 feeding conveyor."""
        return await arduino.send_command("STOP_FEEDING_CONVEYOR")

    async def start_sorting_conveyor(self) -> Dict[str, Any]:
        """Start Stage 3 sorting conveyor."""
        return await arduino.send_command("START_SORTING_CONVEYOR")

    async def stop_sorting_conveyor(self) -> Dict[str, Any]:
        """Stop Stage 3 sorting conveyor."""
        return await arduino.send_command("STOP_SORTING_CONVEYOR")

    async def stop_all_conveyors(self) -> Dict[str, Any]:
        """Halt all conveyors immediately."""
        return await arduino.send_command("STOP_CONVEYOR")

    async def emergency_stop(self) -> Dict[str, Any]:
        """Trigger emergency stop sequence (kill motors and lock actuators)."""
        return await arduino.send_command("EMERGENCY_STOP")

    async def wait_for_arrival(self, timeout_sec: float = 10.0) -> bool:
        """Poll or wait for arrival sensor trigger at the inspection platform."""
        res = await arduino.send_command("WAIT_ARRIVAL", {"timeout": timeout_sec})
        return res.get("success", True)

    async def wait_for_sorting_position(self, timeout_sec: float = 6.0) -> bool:
        """Poll or wait for optical trigger when component reaches the sorting diverter."""
        res = await arduino.send_command("WAIT_SORTING_POSITION", {"timeout": timeout_sec})
        return res.get("success", True)

conveyor_controller = ConveyorController()

