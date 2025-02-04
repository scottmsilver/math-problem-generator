import os
import sys
from typing import List, Optional
import base64
import mimetypes
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
                    mime_type = mimetypes.guess_type(image_path)[0] or 'application/octet-stream'
                    with open(image_path, 'rb') as img:
                        image_data = base64.b64encode(img.read()).decode('utf-8')
                        images.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": image_data
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