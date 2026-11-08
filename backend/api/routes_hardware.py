"""
Inspectra - Hardware Control and Status Endpoints
Exposes controls for the 3 SG90 servos, 2 conveyor stages, and emergency halt.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from ..hardware import arduino, servo_controller, conveyor_controller
from ..config import config
from ..inspection import inspection_manager

router = APIRouter(prefix="/api/hardware", tags=["hardware"])

class OperationModeRequest(BaseModel):
    mode: str # "manual" or "automated"

@router.get("/mode")
def get_operation_mode():
    """Return active operation mode ('manual' or 'automated')."""
    return {
        "mode": config.OPERATION_MODE,
        "is_auto_running": inspection_manager.is_auto_mode
    }

@router.post("/mode")
async def set_operation_mode(req: OperationModeRequest):
    """Switch system operation mode between Manual and Fully Automated."""
    target_mode = req.mode.lower()
    if target_mode not in ["manual", "automated"]:
        return {"error": "Invalid mode. Choose 'manual' or 'automated'."}

    config.update({"OPERATION_MODE": target_mode})

    if target_mode == "automated":
        # Launch closed-loop autonomous background sequence
        await inspection_manager.start_auto_mode()
    else:
        # Halt auto-mode and safely stop all motion
        await inspection_manager.stop_auto_mode()

    return {
        "status": "updated",
        "mode": config.OPERATION_MODE,
        "is_auto_running": inspection_manager.is_auto_mode
    }

class ServoMoveRequest(BaseModel):
    action: str # "rotate_90", "transfer", "divert_nut", "divert_washer", "reset"

class ConveyorControlRequest(BaseModel):
    conveyor_id: int # 1 = feeding, 2 = sorting
    action: str # "start", "stop"

@router.get("/status")
def get_hardware_status():
    """Return live actuator states, serial connection info, and simulation status."""
    return arduino.get_hardware_state()

@router.get("/ports")
def list_serial_ports():
    """List host serial ports for Arduino selection."""
    return arduino.list_available_ports()

@router.post("/servo/control")
async def control_servo(req: ServoMoveRequest):
    """Manually actuate an SG90 servo for testing."""
    if req.action == "rotate_90":
        res = await servo_controller.rotate_component_90()
    elif req.action == "transfer":
        res = await servo_controller.transfer_to_sorting_conveyor()
    elif req.action == "divert_nut":
        res = await servo_controller.divert_to_nut_bin()
    elif req.action == "divert_washer":
        res = await servo_controller.divert_to_washer_bin()
    elif req.action == "reset":
        res = await servo_controller.reset_all_servos()
    else:
        return {"error": f"Unknown servo action {req.action}"}
    return {"status": "ok", "action": req.action, "result": res}

@router.post("/conveyor/control")
async def control_conveyor(req: ConveyorControlRequest):
    """Manually start or stop feeding or sorting conveyor."""
    if req.conveyor_id == 1:
        if req.action == "start":
            res = await conveyor_controller.start_feeding_conveyor()
        else:
            res = await conveyor_controller.stop_feeding_conveyor()
    elif req.conveyor_id == 2:
        if req.action == "start":
            res = await conveyor_controller.start_sorting_conveyor()
        else:
            res = await conveyor_controller.stop_sorting_conveyor()
    else:
        return {"error": f"Invalid conveyor ID {req.conveyor_id}"}
    return {"status": "ok", "conveyor_id": req.conveyor_id, "action": req.action, "result": res}

@router.post("/emergency_stop")
async def trigger_emergency_stop():
    """Halt all conveyors and servos immediately."""
    res = await conveyor_controller.emergency_stop()
    return {"status": "EMERGENCY_STOP_ACTIVE", "result": res}

@router.post("/reset")
async def reset_hardware():
    """Reset actuators and conveyors to baseline home states."""
    res = await servo_controller.reset_all_servos()
    return {"status": "RESET_COMPLETE", "result": res}

