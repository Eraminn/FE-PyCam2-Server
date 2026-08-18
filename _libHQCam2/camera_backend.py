from abc import ABC, abstractmethod


class CameraBackend(ABC):
    """Common interface used by the server command layer.

    The server expects a camera object with a stable set of methods regardless of
    the underlying SDK. This interface keeps the Pi-camera and Basler-camera
    implementations interchangeable.
    """

    camera_name = "generic"

    @staticmethod
    @abstractmethod
    def is_available():
        raise NotImplementedError

    @abstractmethod
    def GetCamera(self):
        raise NotImplementedError

    @abstractmethod
    def CaptureMeta(self):
        raise NotImplementedError

    @abstractmethod
    def CaptureFromStream(self, stream="raw"):
        raise NotImplementedError

    @abstractmethod
    def CaptureMetaAndImgFromStream(self, stream="raw"):
        raise NotImplementedError

    @abstractmethod
    def SetSS(self, ss:int, Lo=0.95, Hi=1.05):
        raise NotImplementedError

    @abstractmethod
    def GetSS(self):
        raise NotImplementedError

    @abstractmethod
    def SetScalerCrop(self, ScalerCropWin=[0, 0, 4056, 3040]):
        raise NotImplementedError

    @abstractmethod
    def GetScalerCrop(self):
        raise NotImplementedError

    @abstractmethod
    def SetAG(self, ag:float=1.0):
        raise NotImplementedError

    @abstractmethod
    def GetAG(self):
        raise NotImplementedError

    @abstractmethod
    def SetAWB(self, awb:tuple=(1.0, 1.0)):
        raise NotImplementedError

    @abstractmethod
    def GetAWB(self):
        raise NotImplementedError

    @abstractmethod
    def SetFD(self, fd:int=100000):
        raise NotImplementedError

    @abstractmethod
    def GetFD(self):
        raise NotImplementedError

    @abstractmethod
    def SetFR(self, fr:float=10.0):
        raise NotImplementedError

    @abstractmethod
    def GetFR(self):
        raise NotImplementedError
