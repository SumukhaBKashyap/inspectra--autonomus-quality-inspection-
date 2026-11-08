"""
Inspectra – Hardware Interface Module.

Communicates with an Arduino over serial (PySerial) using line-delimited
JSON messages.  All commands wait for explicit ACK from Arduino before
returning – the application NEVER assumes a servo has completed movement
without firmware confirmation.

Protocol (host → Arduino): JSON on one line, terminated with \\n
  {"cmd": "CONVEYOR1_START"}
  {"cmd": "SENSOR_READ"}
  {"cmd": "SERVO1_ROTATE", "degrees": 90}
  {"cmd": "SERVO2_PUSH"}
  {"cmd": "SERVO3_MOVE", "position": "NUT_PATH"}   # or WASHER_PATH / STOP

Protocol (Arduino → host): JSON on one line, terminated with \\n
  {"ack": "CONVEYOR1_STARTED"}
  {"ack": "SENSOR_READ", "state": "ARRIVAL"}        # or "EMPTY"
  {"ack": "SERVO1_DONE", "degrees": 90}
  {"ack": "SERVO2_DONE"}
  {"ack": "SERVO3_DONE", "position": "NUT_PATH"}
  {"ack": "SORTING_SENSOR", "state": "DETECTED"}    # or "EMPTY"
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import serial

from . import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serial connection (lazy, singleton)
# ---------------------------------------------------------------------------

_ser: Optional[serial.Serial] = None
_ser_lock = asyncio.Lock()


async def _get_serial() -> serial.Serial:
    """Return (and lazily open) the serial connection to Arduino."""
    global _ser
    async with _ser_lock:
        if _ser is None or not _ser.is_open:
            loop = asyncio.get_event_loop()
            _ser = await loop.run_in_executor(
                None,
                lambda: serial.Serial(
                    config.SERIAL_PORT,
                    config.BAUD_RATE,
                    timeout=config.SERIAL_TIMEOUT,
                )
            )
            # Allow Arduino to reset after DTR toggle
            await asyncio.sleep(2.0)
            logger.info("Serial connection opened on %s @ %d", config.SERIAL_PORT, config.BAUD_RATE)
    return _ser


async def close_serial() -> None:
    """Cleanly close the serial port (call on app shutdown)."""
    global _ser
    async with _ser_lock:
        if _ser and _ser.is_open:
            _ser.close()
            _ser = None


# ---------------------------------------------------------------------------
# Low-level send / receive
# ---------------------------------------------------------------------------

async def _send(payload: Dict[str, Any]) -> None:
    """Serialise *payload* to JSON and write to Arduino."""
    ser = await _get_serial()
    line = json.dumps(payload) + "\n"
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: ser.write(line.encode()))
    logger.debug("→ Arduino: %s", line.strip())


async def _recv_line(timeout: float = 5.0) -> Dict[str, Any]:
    """
    Read one JSON line from Arduino.
    Raises TimeoutError if nothing arrives within *timeout* seconds.
    """
    ser = await _get_serial()
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    while loop.time() < deadline:
        in_waiting = await loop.run_in_executor(None, lambda: ser.in_waiting)
        if in_waiting:
            raw = await loop.run_in_executor(None, ser.readline)
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                logger.debug("← Arduino: %s", line)
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Non-JSON from Arduino: %r", line)
        await asyncio.sleep(0.05)
    raise TimeoutError(f"No response from Arduino within {timeout}s")


async def _send_and_wait(
    payload: Dict[str, Any],
    expected_ack: str,
    timeout: float = 5.0,
) -> Dict[str, Any]:
    """
    Send a command and wait until a response with matching ``ack`` is received.
    All intermediate messages are logged but not returned.
    """
    await _send(payload)
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        resp = await _recv_line(timeout=max(0.1, deadline - asyncio.get_event_loop().time()))
        if resp.get("ack") == expected_ack:
            return resp
        # Log unexpected messages (could be sensor events, debug prints, etc.)
        logger.info("Ignoring Arduino message while waiting for %r: %s", expected_ack, resp)
    raise TimeoutError(
        f"Did not receive ACK '{expected_ack}' from Arduino within {timeout}s"
    )


# ---------------------------------------------------------------------------
# Stage 1 – Feeding
# ---------------------------------------------------------------------------

async def start_conveyor_1() -> None:
    """Start conveyor 1 and wait for Arduino confirmation."""
    await _send_and_wait(
        {"cmd": "CONVEYOR1_START"},
        expected_ack="CONVEYOR1_STARTED",
        timeout=config.SERVO_ACK_TIMEOUT,
    )
    logger.info("Conveyor 1 started.")


async def stop_conveyor_1() -> None:
    """Stop conveyor 1 and wait for Arduino confirmation."""
    await _send_and_wait(
        {"cmd": "CONVEYOR1_STOP"},
        expected_ack="CONVEYOR1_STOPPED",
        timeout=config.SERVO_ACK_TIMEOUT,
    )
    logger.info("Conveyor 1 stopped.")


async def wait_for_component_arrival(
    poll_interval: float = 0.5,
    timeout: float = None,
) -> None:
    """
    Repeatedly poll the arrival sensor until a component is detected.
    Raises TimeoutError if no component arrives within *timeout* seconds.
    """
    if timeout is None:
        timeout = config.ARRIVAL_TIMEOUT

    logger.info("Waiting for component arrival (timeout=%.1fs)…", timeout)
    deadline = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < deadline:
        resp = await _send_and_wait(
            {"cmd": "SENSOR_READ"},
            expected_ack="SENSOR_READ",
            timeout=2.0,
        )
        if resp.get("state") == "ARRIVAL":
            logger.info("Component arrival detected.")
            return
        await asyncio.sleep(poll_interval)

    raise TimeoutError("Component did not arrive within timeout")


async def transfer_to_platform() -> None:
    """
    Activate SG90 #2 (transfer pusher) to move the component from
    conveyor 1 onto the stationary inspection platform.
    Wait for SERVO2_DONE ACK before returning.
    """
    logger.info("Pushing component to inspection platform (SERVO2)…")
    await _send_and_wait(
        {"cmd": "SERVO2_PUSH"},
        expected_ack="SERVO2_DONE",
        timeout=config.SERVO_ACK_TIMEOUT,
    )
    logger.info("Component transferred to inspection platform.")


# ---------------------------------------------------------------------------
# Stage 2 – Inspection helpers
# ---------------------------------------------------------------------------

async def rotate_component_90() -> None:
    """
    Command SG90 #1 to rotate the component 90 degrees.
    Wait for SERVO1_DONE ACK before returning.
    """
    logger.info("Rotating component 90° (SERVO1)…")
    await _send_and_wait(
        {"cmd": "SERVO1_ROTATE", "degrees": 90},
        expected_ack="SERVO1_DONE",
        timeout=config.SERVO_ACK_TIMEOUT,
    )
    logger.info("Component rotation complete.")


def get_latest_images(inspection_id: str, count: int = 2) -> List[str]:
    """
    Return paths of the most recent *count* images stored for *inspection_id*.
    Images are saved to ``media/<inspection_id>/`` by the upload endpoint.
    """
    media_dir = os.path.join(os.getcwd(), "media", inspection_id)
    if not os.path.isdir(media_dir):
        raise FileNotFoundError(
            f"Media directory for inspection {inspection_id!r} not found at {media_dir}"
        )
    files = [
        os.path.join(media_dir, f)
        for f in os.listdir(media_dir)
        if os.path.isfile(os.path.join(media_dir, f))
    ]
    files.sort(key=os.path.getmtime)   # oldest first → view1 then view2
    return files[:count]


# ---------------------------------------------------------------------------
# Stage 3 – Sorting
# ---------------------------------------------------------------------------

async def push_to_conveyor_3() -> None:
    """
    Activate SG90 #2 again to push the inspected component from the
    inspection platform onto conveyor 3 (sorting conveyor).
    Wait for SERVO2_DONE ACK.
    """
    logger.info("Pushing component to sorting conveyor (SERVO2 extended)…")
    await _send_and_wait(
        {"cmd": "SERVO2_PUSH_TO_CONVEYOR3"},
        expected_ack="SERVO2_DONE",
        timeout=config.SERVO_ACK_TIMEOUT,
    )
    logger.info("Component on sorting conveyor.")


async def wait_for_sorting_position(
    poll_interval: float = 0.5,
    timeout: float = None,
) -> None:
    """
    Poll until the component reaches the sorting sensor position on conveyor 3.
    """
    if timeout is None:
        timeout = config.ARRIVAL_TIMEOUT

    logger.info("Waiting for component at sorting position…")
    deadline = asyncio.get_event_loop().time() + timeout

    while asyncio.get_event_loop().time() < deadline:
        resp = await _send_and_wait(
            {"cmd": "SORTING_SENSOR_READ"},
            expected_ack="SORTING_SENSOR",
            timeout=2.0,
        )
        if resp.get("state") == "DETECTED":
            logger.info("Component at sorting position.")
            return
        await asyncio.sleep(poll_interval)

    raise TimeoutError("Component did not reach sorting position within timeout")


async def execute_sorting(outcome: str, component_type: Optional[str] = None) -> None:
    """
    Drive SG90 #3 (sorting stick) based on the application's decision.

    Sorting rules:
        PASS + nut     → NUT_PATH
        PASS + washer  → WASHER_PATH
        PASS + unknown → STOP (manual identification needed)
        FAIL           → STOP (manual rejection)
        REVIEW         → STOP (manual review)
        UNKNOWN        → STOP (manual identification)

    Waits for SERVO3_DONE ACK before returning.
    """
    # Push component from platform to conveyor 3 first
    await push_to_conveyor_3()
    # Wait until it reaches the sorting sensor
    await wait_for_sorting_position()

    # Determine sorting position
    if outcome == "PASS":
        if component_type == "nut":
            position = "NUT_PATH"
        elif component_type == "washer":
            position = "WASHER_PATH"
        else:
            position = "STOP"
            logger.warning("PASS but unknown component type – stopping for manual ID.")
    else:
        # FAIL, REVIEW, UNKNOWN → all stop for manual intervention
        position = "STOP"
        logger.info("Sorting position=STOP (outcome=%s).", outcome)

    logger.info("Moving sorting stick to %s (SERVO3)…", position)
    await _send_and_wait(
        {"cmd": "SERVO3_MOVE", "position": position},
        expected_ack="SERVO3_DONE",
        timeout=config.SERVO_ACK_TIMEOUT,
    )
    logger.info("Sorting complete: position=%s.", position)
