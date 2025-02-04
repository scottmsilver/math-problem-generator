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
        # Model will be set in execute() based on whether images are provided
        self.model = None

    def execute(self, prompt: str, image_paths: Optional[List[str]] = None) -> str:
        try:
            # Select appropriate model based on whether we have images
            model_name = 'gemini-pro-vision' if image_paths else 'gemini-pro'
            self.model = genai.GenerativeModel(model_name)

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

            # Ensure the response is not blocked
            if response.prompt_feedback.block_reason:
                raise Exception(f"Response blocked: {response.prompt_feedback.block_reason}")

            # Process response parts
            if hasattr(response, 'parts'):
                return ' '.join(part.text for part in response.parts)
            elif hasattr(response, 'candidates'):
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        return candidate.content.parts[0].text

            raise Exception("No valid response content found")

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")