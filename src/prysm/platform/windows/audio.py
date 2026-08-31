import logging
from typing import Protocol

try:
    from ctypes import POINTER, cast

    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False

logger = logging.getLogger(__name__)


class AudioController(Protocol):
    async def get_volume(self) -> int: ...
    async def set_volume(self, level: int) -> None: ...
    async def mute(self) -> None: ...
    async def unmute(self) -> None: ...


class WindowsAudioController:
    """Windows implementation of the AudioController using pycaw."""

    def _get_interface(self):
        if not PYCAW_AVAILABLE:
            raise RuntimeError("pycaw is not installed or available.")
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(  # type: ignore
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        return cast(interface, POINTER(IAudioEndpointVolume))

    async def get_volume(self) -> int:
        try:
            interface = self._get_interface()
            # GetMasterVolumeLevelScalar returns a float 0.0 - 1.0
            scalar = interface.GetMasterVolumeLevelScalar()  # type: ignore
            return int(round(scalar * 100))
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return 0

    async def set_volume(self, level: int) -> None:
        try:
            interface = self._get_interface()
            scalar = max(0.0, min(1.0, level / 100.0))
            interface.SetMasterVolumeLevelScalar(scalar, None)  # type: ignore
            logger.debug(f"Set master volume to {level}%")
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")

    async def mute(self) -> None:
        try:
            interface = self._get_interface()
            interface.SetMute(1, None)  # type: ignore
            logger.debug("Muted master volume")
        except Exception as e:
            logger.error(f"Failed to mute: {e}")

    async def unmute(self) -> None:
        try:
            interface = self._get_interface()
            interface.SetMute(0, None)  # type: ignore
            logger.debug("Unmuted master volume")
        except Exception as e:
            logger.error(f"Failed to unmute: {e}")
