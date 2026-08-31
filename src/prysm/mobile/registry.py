import json
import logging
import os
import time

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PairedDevice(BaseModel):
    device_id: str
    name: str
    platform: str
    shared_secret_b64: str
    paired_at: float = time.time()
    last_seen: float = time.time()
    capabilities: list[str] = []


class DeviceRegistry:
    def __init__(self, data_path: str = "data/devices.json"):
        self.data_path = data_path
        self._devices: dict[str, PairedDevice] = {}
        self._load()

    def _load(self):
        if not os.path.exists(self.data_path):
            return
        try:
            with open(self.data_path, encoding="utf-8") as f:
                data = json.load(f)
                for did, dev_dict in data.items():
                    self._devices[did] = PairedDevice(**dev_dict)
        except Exception as e:
            logger.error(f"Failed to load device registry: {e}")

    def _save(self):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.data_path)), exist_ok=True)
            with open(self.data_path, "w", encoding="utf-8") as f:
                json.dump(
                    {k: v.model_dump() for k, v in self._devices.items()}, f, indent=2
                )
        except Exception as e:
            logger.error(f"Failed to save device registry: {e}")

    def add_device(self, device: PairedDevice):
        self._devices[device.device_id] = device
        self._save()

    def remove_device(self, device_id: str):
        if device_id in self._devices:
            del self._devices[device_id]
            self._save()

    def get_device(self, device_id: str) -> PairedDevice | None:
        return self._devices.get(device_id)

    def update_last_seen(self, device_id: str):
        if device_id in self._devices:
            self._devices[device_id].last_seen = time.time()
            self._save()

    def get_all_devices(self) -> list[PairedDevice]:
        return list(self._devices.values())
