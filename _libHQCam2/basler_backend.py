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
        self._bayer_pattern = "RG"
        self._pixel_format = "BayerRG12"
        self._initialize_camera(fr)

    def _initialize_camera(self, fr:float):
        tl_factory = pylon.TlFactory.GetInstance()
        devices = tl_factory.EnumerateDevices()
        if not devices:
            raise RuntimeError("No Basler cameras were detected via pypylon.")

        self._camera = pylon.InstantCamera(tl_factory.CreateFirstDevice())
        self._camera.Open()

        # Default to full frame but keep the ROI adjustable.
        if hasattr(self._camera, "Width"):
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

    @staticmethod
    def _normalize_bayer_image(image):
        arr = np.asarray(image)
        if arr.ndim == 3 and arr.shape[-1] == 1:
            arr = arr[:, :, 0]
        if arr.dtype != np.uint16:
            arr = arr.astype(np.uint16, copy=False)
        return arr

    def CaptureMeta(self):
        return {
            "ExposureTime": self.GetSS(),
            "AnalogueGain": self.GetAG(),
            "ColourGains": self.GetAWB(),
            "FrameDuration": self.GetFD(),
            "ScalerCrop": self.GetScalerCrop(),
            "BayerPattern": self._bayer_pattern,
            "PixelFormat": self._pixel_format,
        }

    def CaptureFromStream(self, stream="raw"):
        img = self._retrieve_image()
        if img is None:
            raise RuntimeError("Basler camera returned no image data.")
        stream_name = str(stream).lower()
        if stream_name in ("raw", "bayer", "sensor"):
            return self._normalize_bayer_image(img)
        return self._normalize_bayer_image(img)

    def CaptureMetaAndImgFromStream(self, stream="raw"):
        return self.CaptureFromStream(stream=stream), self.CaptureMeta()

    def SetSS(self, ss:int, Lo=0.95, Hi=1.05):
        if hasattr(self._camera, "ExposureTime"):
            prop = self._camera.ExposureTime
            min_value = getattr(prop, "Min", 0.0)
            max_value = getattr(prop, "Max", float(ss))
            clamped_value = min(float(max_value), max(float(min_value), float(ss)))
            prop.SetValue(clamped_value)
        return 0

    def GetSS(self):
        if hasattr(self._camera, "ExposureTime"):
            return float(self._camera.ExposureTime.GetValue())
        return 0.0

    def SetScalerCrop(self, ScalerCropWin=[0, 0, 4056, 3040]):
        x, y, w, h = [int(v) for v in ScalerCropWin]
        sensor_w = int(getattr(getattr(self._camera, "Width", None), "Max", max(1, w)))
        sensor_h = int(getattr(getattr(self._camera, "Height", None), "Max", max(1, h)))

        x = max(0, min(x, max(0, sensor_w - 1)))
        y = max(0, min(y, max(0, sensor_h - 1)))
        w = max(1, min(w, max(1, sensor_w - x)))
        h = max(1, min(h, max(1, sensor_h - y)))

        if hasattr(self._camera, "OffsetX"):
            self._camera.OffsetX.SetValue(x)
        if hasattr(self._camera, "OffsetY"):
            self._camera.OffsetY.SetValue(y)
        if hasattr(self._camera, "Width"):
            self._camera.Width.SetValue(w)
        if hasattr(self._camera, "Height"):
            self._camera.Height.SetValue(h)
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
        self._awb = (float(red_gain), float(blue_gain))
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
                self._awb = (red_gain, blue_gain)
                return (red_gain, blue_gain)
            except Exception:
                pass
        return getattr(self, "_awb", (1.0, 1.0))

    def _acquisition_rate_property_name(self):
        for prop_name in ("AcquisitionFrameRateAbs", "AcquisitionFrameRate"):
            if hasattr(self._camera, prop_name):
                return prop_name
        return None

    def SetFD(self, fd:int=100000):
        # fd is treated as the sensor frame duration in microseconds for compatibility
        # with the existing server API.
        if fd <= 0:
            return 0
        self.SetFR(1_000_000.0 / float(fd))
        return 0

    def GetFD(self):
        frame_rate = self.GetFR()
        if frame_rate <= 0:
            return 100000.0
        return 1_000_000.0 / float(frame_rate)

    def SetFR(self, fr:float=10.0):
        if hasattr(self._camera, "AcquisitionFrameRateEnable"):
            try:
                self._camera.AcquisitionFrameRateEnable.SetValue(True)
            except Exception:
                pass

        rate_prop_name = self._acquisition_rate_property_name()
        if rate_prop_name is not None:
            try:
                getattr(self._camera, rate_prop_name).SetValue(float(fr))
            except Exception:
                pass

        if hasattr(self._camera, "ResultingFrameRate"):
            try:
                self._camera.ResultingFrameRate.SetValue(float(fr))
            except Exception:
                pass
        return 0

    def GetFR(self):
        for prop_name in ("ResultingFrameRate", "AcquisitionFrameRateAbs", "AcquisitionFrameRate"):
            if hasattr(self._camera, prop_name):
                try:
                    return float(getattr(self._camera, prop_name).GetValue())
                except Exception:
                    pass
        return 10.0
