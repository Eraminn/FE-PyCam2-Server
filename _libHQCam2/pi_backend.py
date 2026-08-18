from _libHQCam2.camera_backend import CameraBackend


class PiCameraBackend(CameraBackend):
    """Compatibility wrapper around the existing Raspberry Pi camera backend."""

    camera_name = "Raspberry Pi HQ Camera"

    @staticmethod
    def is_available():
        try:
            # Local import keeps this optional and prevents hard dependency issues
            from picamera2 import Picamera2  # noqa: F401
            return True
        except Exception:
            return False

    def __init__(self, fr:float=10.0, awaitWarmup:float=1.0):
        from _libHQCam2.PyCam2 import PyCam2
        self._impl = PyCam2(fr=fr, awaitWarmup=awaitWarmup)

    def GetCamera(self):
        return self._impl.GetCamera()

    def CaptureMeta(self):
        return self._impl.CaptureMeta()

    def CaptureFromStream(self, stream="raw"):
        return self._impl.CaptureFromStream(stream=stream)

    def CaptureMetaAndImgFromStream(self, stream="raw"):
        return self._impl.CaptureMetaAndImgFromStream(stream=stream)

    def SetSS(self, ss:int, Lo=0.95, Hi=1.05):
        return self._impl.SetSS(ss, Lo=Lo, Hi=Hi)

    def GetSS(self):
        return self._impl.GetSS()

    def SetScalerCrop(self, ScalerCropWin=[0, 0, 4056, 3040]):
        return self._impl.SetScalerCrop(ScalerCropWin)

    def GetScalerCrop(self):
        return self._impl.GetScalerCrop()

    def SetAG(self, ag:float=1.0):
        return self._impl.SetAG(ag)

    def GetAG(self):
        return self._impl.GetAG()

    def SetAWB(self, awb:tuple=(1.0, 1.0)):
        return self._impl.SetAWB(awb)

    def GetAWB(self):
        return self._impl.GetAWB()

    def SetFD(self, fd:int=100000):
        return self._impl.SetFD(fd)

    def GetFD(self):
        return self._impl.GetFD()

    def SetFR(self, fr:float=10.0):
        return self._impl.SetFR(fr)

    def GetFR(self):
        return self._impl.GetFR()
