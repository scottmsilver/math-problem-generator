import os
from typing import List, Optional
import google.generativeai as genai
from . import LLMProvider
import PyPDF2
import tempfile
import base64

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable must be set")

        genai.configure(api_key=self.api_key)
        self.model = None

    def _read_file_content(self, file_path: str) -> str:
        """Read content from a file, handling both text and PDF files."""
        try:
            if file_path.lower().endswith('.pdf'):
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    return text
            else:
                try:
                    # Try UTF-8 first
                    with open(file_path, 'r', encoding='utf-8') as file:
                        return file.read()
                except UnicodeDecodeError:
                    # Fall back to latin-1 if UTF-8 fails
                    with open(file_path, 'r', encoding='latin-1') as file:
                        return file.read()
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")

    def execute(self, prompt: str, file_paths: Optional[List[str]] = None) -> str:
        try:
            # Always use text-only model since we're working with LaTeX
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # If files are provided, read their contents and append to prompt
            if file_paths:
                full_prompt = prompt + "\n\nReference content:\n"
                for file_path in file_paths:
                    try:
                        content = self._read_file_content(file_path)
                        # Clean the content to ensure it's valid UTF-8
                        content = content.encode('utf-8', errors='ignore').decode('utf-8')
                        full_prompt += f"\n{content}\n"
                    except Exception as e:
                        raise Exception(f"Error processing file {file_path}: {str(e)}")
            else:
                full_prompt = prompt

            # Add instruction to not use code blocks
            full_prompt += "\n\nIMPORTANT: Return ONLY the LaTeX code without any markdown code blocks or backticks."

            # Generate response
            response = self.model.generate_content(full_prompt)

            # Ensure the response is not blocked
            if response.prompt_feedback.block_reason:
                raise Exception(f"Response blocked: {response.prompt_feedback.block_reason}")

            # Process response parts and clean up any remaining code blocks
            if hasattr(response, 'parts'):
                text = ' '.join(part.text for part in response.parts)
            elif hasattr(response, 'candidates'):
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        text = candidate.content.parts[0].text
                        break
            else:
                raise Exception("No valid response content found")
                
            # Clean up any remaining code blocks or backticks
            text = text.replace('```latex', '').replace('```', '').replace('`', '')
            return text.strip()

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")