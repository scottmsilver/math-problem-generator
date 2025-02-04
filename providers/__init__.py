from abc import ABC, abstractmethod
from typing import List, Optional

class LLMProvider(ABC):
    @abstractmethod
    def execute(self, prompt: str, image_paths: Optional[List[str]] = None) -> str:
        """Execute the prompt with the LLM provider."""
        pass
