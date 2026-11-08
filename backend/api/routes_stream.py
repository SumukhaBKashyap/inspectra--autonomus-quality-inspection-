"""
Inspectra - Camera MJPEG Stream Endpoint
Streams live video frames from Android IP Webcam, USB Camera, or simulated feed.
"""

import time
import cv2
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse
from ..vision import camera_manager

router = APIRouter(prefix="/api/stream", tags=["stream"])

def generate_mjpeg_stream():
    """Generator yielding multipart JPEG frames."""
    while True:
        frame = camera_manager.get_frame()
        if frame is not None:
            ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ret:
                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )
        time.sleep(0.04) # ~25 fps

@router.get("/video_feed")
def video_feed():
    """MJPEG stream endpoint for frontend video player."""
    return StreamingResponse(
        generate_mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@router.get("/snapshot")
def get_snapshot():
    """Return single current JPEG snapshot."""
    frame = camera_manager.get_frame()
    if frame is None:
        return Response(content=b"", status_code=503)
    ret, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ret:
        return Response(content=b"", status_code=500)
    return Response(content=buffer.tobytes(), media_type="image/jpeg")

