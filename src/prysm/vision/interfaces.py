from abc import ABC, abstractmethod
from typing import Any


class VisionAnalyzer(ABC):
    """Abstract base class for computer vision analysis."""
    
    @abstractmethod
    async def analyze_image(self, image_data: bytes) -> Any:
        pass
