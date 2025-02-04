import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class Logger:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self._setup_log_directory()

    def _setup_log_directory(self) -> None:
        """Create the log directory if it doesn't exist."""
        os.makedirs(self.log_dir, exist_ok=True)

    def log_interaction(
        self,
        model: str,
        prompt: str,
        variables: Dict[str, str],
        images: Optional[List[str]] = None,
        response: Optional[str] = None
    ) -> None:
        """
        Log an LLM interaction to a JSON file.
        
        Args:
            model: Name of the LLM model used
            prompt: The processed prompt
            variables: Dictionary of template variables
            images: List of image paths used
            response: The model's response
        """
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "model": model,
            "prompt": prompt,
            "variables": variables,
            "images": images or [],
            "response": response
        }

        filename = f"interaction_{timestamp.replace(':', '-')}.json"
        log_path = os.path.join(self.log_dir, filename)

        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)

def setup_logging(log_dir: str) -> Logger:
    """
    Setup and return a Logger instance.
    
    Args:
        log_dir: Directory to store logs
        
    Returns:
        Logger instance
    """
    return Logger(log_dir)
