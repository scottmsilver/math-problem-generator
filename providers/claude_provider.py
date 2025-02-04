import os
import sys
from typing import List, Optional
import base64
import mimetypes
import anthropic
from anthropic import Anthropic
from . import LLMProvider
import PyPDF2

class ClaudeProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def execute(self, prompt: str, file_paths: Optional[List[str]] = None) -> str:
        try:
            if file_paths:
                # Prepare files for multimodal input
                content_items = []
                for file_path in file_paths:
                    # Use .tex extension for LaTeX files
                    if file_path.endswith('.tex'):
                        mime_type = 'text/plain'
                    else:
                        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                    
                    # Handle different file types
                    if mime_type == 'application/pdf':
                        with open(file_path, 'rb') as f:
                            file_data = base64.b64encode(f.read()).decode('utf-8')
                            content_items.append({
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": file_data
                                }
                            })
                    elif mime_type.startswith('text/'):
                        # For text files, just read the content
                        with open(file_path, 'r') as f:
                            content_items.append({
                                "type": "text",
                                "text": f.read()
                            })
                    else:
                        # For images and other files
                        with open(file_path, 'rb') as f:
                            file_data = base64.b64encode(f.read()).decode('utf-8')
                            content_items.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": file_data
                                }
                            })

                # Add the prompt as text content
                content_items.append({
                    "type": "text",
                    "text": prompt
                })

                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": content_items
                    }]
                )
            else:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

            return message.content[0].text

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")