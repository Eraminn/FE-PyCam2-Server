import unittest

import numpy as np

from _libHQCam2 import basler_backend


class DummyProperty:
    def __init__(self, value=0.0, maximum=None, minimum=0.0):
        self.value = value
        self.Max = maximum if maximum is not None else value
        self.Min = minimum

    def SetValue(self, value):
        self.value = value

    def GetValue(self):
        return self.value

    def TrySetToMaximum(self):
        self.value = self.Max


class DummyResult:
    def __init__(self, array):
        self.Array = array

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def GrabSucceeded(self):
        return True


class DummyCamera:
    def __init__(self, fr=10.0):
        self.Width = DummyProperty(5320, 5320)
        self.Height = DummyProperty(3032, 3032)
        self.OffsetX = DummyProperty(0, 5320)
        self.OffsetY = DummyProperty(0, 3032)
        self.PixelFormat = DummyProperty(0)
        self.ExposureTime = DummyProperty(10000.0, 1_000_000.0, 1.0)
        self.Gain = DummyProperty(1.0, 20.0)
        self.AcquisitionFrameRateEnable = DummyProperty(False)
        self.AcquisitionFrameRate = DummyProperty(fr, fr)
        self.ResultingFrameRate = DummyProperty(fr, fr)
        self.BalanceRatioSelector = DummyProperty("Red")
        self.BalanceRatio = DummyProperty(1.0, 10.0)
        self._grabbed = False

    def Open(self):
        return None

    def StartGrabbing(self, *args, **kwargs):
        self._grabbed = True

    def RetrieveResult(self, timeout, handling):
        return DummyResult(np.zeros((8, 8), dtype=np.uint16))

    def SetValue(self, value):
        self.value = float(value)


class DummyTlFactory:
    def __init__(self, camera):
        self._camera = camera

    def EnumerateDevices(self):
        return ["camera"]

    def CreateFirstDevice(self):
        return self._camera


class DummyPylonModule:
    GrabStrategy_OneByOne = "one-by-one"
    TimeoutHandling_ThrowException = "throw"

    class TlFactory:
        _instance = None

        @classmethod
        def GetInstance(cls):
            if cls._instance is None:
                cls._instance = DummyTlFactory(DummyCamera())
            return cls._instance

    @classmethod
    def InstantCamera(cls, camera):
        return camera


class BaslerBackendCompatibilityTests(unittest.TestCase):
    def test_set_fr_updates_acquisition_rate_property(self):
        original_pylon = basler_backend.pylon
        basler_backend.pylon = DummyPylonModule
        try:
            camera = basler_backend.BaslerCameraBackend(fr=12.5)
            camera.SetFR(25.0)
            self.assertEqual(camera.GetFR(), 25.0)
            self.assertEqual(camera._camera.AcquisitionFrameRate.GetValue(), 25.0)
        finally:
            basler_backend.pylon = original_pylon

    def test_set_ss_and_crop_are_clamped_to_supported_ranges(self):
        original_pylon = basler_backend.pylon
        basler_backend.pylon = DummyPylonModule
        try:
            camera = basler_backend.BaslerCameraBackend(fr=12.5)
            camera.SetSS(10_000_000)
            self.assertEqual(camera.GetSS(), 1_000_000.0)

            camera.SetScalerCrop([5000, 4000, 7000, 5000])
            self.assertEqual(camera.GetScalerCrop(), [5000, 3031, 320, 1])
        finally:
            basler_backend.pylon = original_pylon

    def test_capture_keeps_raw_bayer_metadata(self):
        original_pylon = basler_backend.pylon
        basler_backend.pylon = DummyPylonModule
        try:
            camera = basler_backend.BaslerCameraBackend(fr=12.5)
            img, meta = camera.CaptureMetaAndImgFromStream(stream="raw")
            self.assertEqual(img.dtype, np.uint16)
            self.assertIn("BayerPattern", meta)
            self.assertEqual(meta["BayerPattern"], "RG")
        finally:
            basler_backend.pylon = original_pylon


if __name__ == "__main__":
    unittest.main()
