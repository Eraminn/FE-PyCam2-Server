from __future__ import annotations

import numpy as np

from _libHQCam2.camera_backend import CameraBackend

try:
    from pypylon import pylon
except ImportError:  # pragma: no cover - optional dependency
    pylon = None


class BaslerCameraBackend(CameraBackend):
    """Basler ace 2 R backend using the pypylon GenICam API."""

    camera_name = "Basler ace 2 R"

    @staticmethod
    def is_available():
        if pylon is None:
            return False
        try:
            return len(pylon.TlFactory.GetInstance().EnumerateDevices()) > 0
        except Exception:
            return False

    def __init__(self, fr:float=10.0):
        if pylon is None:
            raise RuntimeError("pypylon is not installed. Install Basler's python package first.")

        self._camera = None
        self._initialize_camera(fr)

    def _initialize_camera(self, fr:float):
        tl_factory = pylon.TlFactory.GetInstance()
        devices = tl_factory.EnumerateDevices()
        if not devices:
            raise RuntimeError("No Basler cameras were detected via pypylon.")

        self._camera = pylon.InstantCamera(tl_factory.CreateFirstDevice())
        self._camera.Open()

        # Default to full frame but keep the ROI adjustable.
        if hasattr(self._camera, "Width") and hasattr(self._camera, "Width"):
            self._camera.Width.SetValue(int(self._camera.Width.Max))
        if hasattr(self._camera, "Height"):
            self._camera.Height.SetValue(int(self._camera.Height.Max))
        if hasattr(self._camera, "OffsetX"):
            self._camera.OffsetX.SetValue(0)
        if hasattr(self._camera, "OffsetY"):
            self._camera.OffsetY.SetValue(0)

        # Some Basler models default to monochrome or Bayer. This keeps the backend
        # working with the unprocessed sensor data expected by the server.
        if hasattr(self._camera, "PixelFormat"):
            try:
                self._camera.PixelFormat.SetValue("BayerRG12")
            except Exception:
                try:
                    self._camera.PixelFormat.SetValue("Mono12")
                except Exception:
                    pass

        if hasattr(self._camera, "ExposureTime"):
            self._camera.ExposureTime.SetValue(10000.0)
        if hasattr(self._camera, "Gain"):
            self._camera.Gain.SetValue(1.0)

        self._camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

        # Generic compatibility: configure the camera to the requested framerate.
        self.SetFR(fr)

    def GetCamera(self):
        return self._camera

    def _retrieve_image(self):
        if self._camera is None:
            raise RuntimeError("Basler camera is not initialized.")

        with self._camera.RetrieveResult(1000, pylon.TimeoutHandling_ThrowException) as result:
            if not result.GrabSucceeded():
                raise RuntimeError("Basler grab failed.")
            return result.Array

    def CaptureMeta(self):
        return {
            "ExposureTime": self.GetSS(),
            "AnalogueGain": self.GetAG(),
            "ColourGains": self.GetAWB(),
            "FrameDuration": self.GetFD(),
            "ScalerCrop": self.GetScalerCrop(),
        }

    def CaptureFromStream(self, stream="raw"):
        img = self._retrieve_image()
        if img is None:
            raise RuntimeError("Basler camera returned no image data.")
        return np.asarray(img)

    def CaptureMetaAndImgFromStream(self, stream="raw"):
        return self.CaptureFromStream(stream=stream), self.CaptureMeta()

    def SetSS(self, ss:int, Lo=0.95, Hi=1.05):
        if hasattr(self._camera, "ExposureTime"):
            self._camera.ExposureTime.SetValue(float(ss))
        return 0

    def GetSS(self):
        if hasattr(self._camera, "ExposureTime"):
            return float(self._camera.ExposureTime.GetValue())
        return 0.0

    def SetScalerCrop(self, ScalerCropWin=[0, 0, 4056, 3040]):
        x, y, w, h = [int(v) for v in ScalerCropWin]
        if hasattr(self._camera, "OffsetX"):
            self._camera.OffsetX.SetValue(max(0, x))
        if hasattr(self._camera, "OffsetY"):
            self._camera.OffsetY.SetValue(max(0, y))
        if hasattr(self._camera, "Width"):
            self._camera.Width.SetValue(max(1, w))
        if hasattr(self._camera, "Height"):
            self._camera.Height.SetValue(max(1, h))
        return 0

    def GetScalerCrop(self):
        x = int(self._camera.OffsetX.GetValue()) if hasattr(self._camera, "OffsetX") else 0
        y = int(self._camera.OffsetY.GetValue()) if hasattr(self._camera, "OffsetY") else 0
        w = int(self._camera.Width.GetValue()) if hasattr(self._camera, "Width") else 0
        h = int(self._camera.Height.GetValue()) if hasattr(self._camera, "Height") else 0
        return [x, y, w, h]

    def SetAG(self, ag:float=1.0):
        if hasattr(self._camera, "Gain"):
            self._camera.Gain.SetValue(float(ag))
        return 0

    def GetAG(self):
        if hasattr(self._camera, "Gain"):
            return float(self._camera.Gain.GetValue())
        return 1.0

    def SetAWB(self, awb:tuple=(1.0, 1.0)):
        red_gain, blue_gain = tuple(awb)
        if hasattr(self._camera, "BalanceRatioSelector") and hasattr(self._camera, "BalanceRatio"):
            for selector, value in (("Red", red_gain), ("Blue", blue_gain)):
                try:
                    self._camera.BalanceRatioSelector.SetValue(selector)
                    self._camera.BalanceRatio.SetValue(float(value))
                except Exception:
                    pass
        return 0

    def GetAWB(self):
        if hasattr(self._camera, "BalanceRatioSelector") and hasattr(self._camera, "BalanceRatio"):
            try:
                self._camera.BalanceRatioSelector.SetValue("Red")
                red_gain = float(self._camera.BalanceRatio.GetValue())
                self._camera.BalanceRatioSelector.SetValue("Blue")
                blue_gain = float(self._camera.BalanceRatio.GetValue())
                return (red_gain, blue_gain)
            except Exception:
                pass
        return (1.0, 1.0)

    def SetFD(self, fd:int=100000):
        # fd is treated as the sensor frame duration in microseconds for compatibility
        # with the existing server API.
        if hasattr(self._camera, "AcquisitionFrameRateEnable"):
            try:
                self._camera.AcquisitionFrameRateEnable.SetValue(True)
            except Exception:
                pass
        if hasattr(self._camera, "AcquisitionFrameRateAbs"):
            try:
                frame_rate = 1_000_000.0 / max(1.0, float(fd))
                self._camera.AcquisitionFrameRateAbs.SetValue(frame_rate)
            except Exception:
                pass
        return 0

    def GetFD(self):
        if hasattr(self._camera, "ResultingFrameRate"):
            try:
                return 1_000_000.0 / float(self._camera.ResultingFrameRate.GetValue())
            except Exception:
                pass
        return 100000.0

    def SetFR(self, fr:float=10.0):
        if hasattr(self._camera, "AcquisitionFrameRateEnable"):
            try:
                self._camera.AcquisitionFrameRateEnable.SetValue(True)
            except Exception:
                pass
        if hasattr(self._camera, "AcquisitionFrameRateAbs"):
            try:
                self._camera.AcquisitionFrameRateAbs.SetValue(float(fr))
            except Exception:
                pass
        return 0

    def GetFR(self):
        if hasattr(self._camera, "ResultingFrameRate"):
            try:
                return float(self._camera.ResultingFrameRate.GetValue())
            except Exception:
                pass
        return 10.0
