import os
from typing import List
from PIL import Image

def validate_image_paths(image_paths: List[str]) -> None:
    """
    Validate image paths and formats.
    
    Args:
        image_paths: List of paths to image files
        
    Raises:
        ValueError: If any image path is invalid or format is unsupported
    """
    supported_formats = {'.jpg', '.jpeg', '.png', '.gif'}
    
    for path in image_paths:
        if not os.path.exists(path):
            raise ValueError(f"Image file not found: {path}")
        
        if not os.path.isfile(path):
            raise ValueError(f"Not a file: {path}")
            
        file_ext = os.path.splitext(path)[1].lower()
        if file_ext not in supported_formats:
            raise ValueError(f"Unsupported image format for {path}. Supported formats: {supported_formats}")
            
        try:
            with Image.open(path) as img:
                img.verify()
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image file {path}: {str(e)}")
