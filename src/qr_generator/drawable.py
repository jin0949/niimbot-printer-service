from abc import ABC, abstractmethod
from PIL import Image


class Drawable(ABC):
    @abstractmethod
    def draw(self) -> Image.Image:
        pass