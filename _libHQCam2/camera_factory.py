from __future__ import annotations

from _libHQCam2.basler_backend import BaslerCameraBackend
from _libHQCam2.pi_backend import PiCameraBackend


def create_camera_backend(fr:float=10.0, prefer:str="auto"):
    """Auto-select the active camera backend.

    Order of preference:
    1) Basler if a Basler device is connected
    2) Raspberry Pi camera if a libcamera device is available
    3) otherwise raise a clear error

    The returned object exposes the same methods expected by the server layer,
    so the rest of the application remains unchanged.
    """
    if prefer == "basler":
        if not BaslerCameraBackend.is_available():
            raise RuntimeError("Basler camera selected but no Basler device was found.")
        return BaslerCameraBackend(fr=fr)

    if prefer == "pi":
        if not PiCameraBackend.is_available():
            raise RuntimeError("Pi camera selected but libcamera/picamera2 is not available.")
        return PiCameraBackend(fr=fr)

    if BaslerCameraBackend.is_available():
        return BaslerCameraBackend(fr=fr)

    if PiCameraBackend.is_available():
        return PiCameraBackend(fr=fr)

    raise RuntimeError(
        "No supported camera was detected. Connect a Basler camera or a Raspberry Pi Camera and retry."
    )
