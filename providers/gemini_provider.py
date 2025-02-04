import os
from typing import List, Optional
import google.generativeai as genai
from . import LLMProvider

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable must be set")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision' if image_paths else 'gemini-pro')

    def execute(self, prompt: str, image_paths: Optional[List[str]] = None) -> str:
        try:
            if image_paths:
                image_parts = []
                for image_path in image_paths:
                    with open(image_path, 'rb') as img:
                        image_parts.append({
                            "mime_type": "image/jpeg",
                            "data": img.read()
                        })
                
                response = self.model.generate_content([prompt, *image_parts])
            else:
                response = self.model.generate_content(prompt)

            return response.text

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
