import os
import sys
from typing import List, Optional
import anthropic
from anthropic import Anthropic
from . import LLMProvider

class ClaudeProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")
        
        # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def execute(self, prompt: str, image_paths: Optional[List[str]] = None) -> str:
        try:
            if image_paths:
                # Prepare images for multimodal input
                images = []
                for image_path in image_paths:
                    with open(image_path, 'rb') as img:
                        images.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img.read()
                            }
                        })
                
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            *images
                        ]
                    }]
                )
            else:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

            return message.content[0].text

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
