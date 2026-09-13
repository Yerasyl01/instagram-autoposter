import requests
import base64
import re
import json
import logging
from typing import Dict, Optional
from pathlib import Path
from config import OPENROUTER_API_KEY, get_image_prompt, get_caption_prompt, SERVICES
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """
    Client for interacting with OpenRouter API.
    Handles both image generation (Meta Muse) and text generation (Ling 3.0 Flash Fin).
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP Referer": "https://openrouter.ai",
            "X-Model-Info-ZU": "1"  # Enable model info
        }

    def generate_image_with_muse(
        self,
        prompt: str,
        reference_image_path: Optional[str] = None,
        width: int = 1080,
        height: int = 1350
    ) -> Optional[str]:
        """
        Generate an Instagram advertisement image using Meta Muse model.
        
        Args:
            prompt: The text prompt for image generation
            reference_image_path: Optional path to reference image for brand consistency
            width: Image width (default 1080 for Instagram portrait)
            height: Image height (default 1350 for Instagram portrait)
        
        Returns:
            Base64 encoded image data or None on failure
        """
        try:
            payload = {
                "model" : "meta/muse-image",
                "prompt": prompt
            }
            if reference_image_path:
                reference_data = self._encode_image(reference_image_path)
                payload["reference_image"] = reference_data

            # Make API request
            response = requests.post(
                f"{self.BASE_URL}/images",
                headers=self.headers,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    # Extract b64_json from the data array
                    image_data = result["data"][0].get("b64_json")
                    if image_data:
                        return image_data
                    else:
                        logger.error("No b64_json found in response")
                        logger.error(f"Response: {result}")
                        return None
                else:
                    logger.error("Unexpected response format")
                    logger.error(f"Response: {result}")
                    return None
            else:
                logger.error(f"Image generation failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
        
        return None

    def generate_caption_with_ling(
        self,
        prompt: str
    ) -> Optional[str]:
        """
        Generate an Instagram caption using Ling 3.0 Flash Fin.
        """

        try:
            payload = {
                "model": "inclusionai/ling-3.0-flash-fin:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 3000,
                "temperature": 0.7
            }

            response = requests.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                logger.error(
                    "Caption generation failed: %s",
                    response.status_code
                )
                logger.error("Response: %s", response.text)
                return None

            result = response.json()

            choices = result.get("choices", [])
            if not choices:
                logger.error("No choices returned by model")
                return None

            logger.info("Ling finish_reason: %s", choices[0].get("finish_reason"))
            logger.info("Ling usage: %s", result.get("usage"))

            message = choices[0].get("message", {})

            # Normal OpenAI/OpenRouter response
            content = message.get("content")

            if content:
                return content.strip()

            # Ling currently appears to put its generated text in reasoning.
            reasoning = message.get("reasoning")

            if not reasoning:
                logger.error("Model returned neither content nor reasoning")
                return None

            logger.warning("Model returned no content; extracting caption from reasoning:\n%s", reasoning)

            # Find the final draft before the final polishing/checking section.
            match = re.search(
                r"\*Draft\s+\d+:\*\s*(.*?)(?=\n\s*\d+\.\s+\*\*Final Polish)",
                reasoning,
                re.DOTALL
            )

            if not match:
                logger.error(
                    "Could not find final draft in model output. "
                    "Reasoning:\n%s",
                    reasoning
                )
                return None

            return match.group(1).strip()

        except Exception as e:
            logger.exception("Error generating caption")
            return None

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def save_image(self, image_data: str, output_path: str) -> bool:
        """
        Save base64 encoded image data to file.
        
        Args:
            image_data: Base64 encoded image string
            output_path: Path to save the image
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # image_data is the base64 string from b64_json
            if not image_data:
                logger.error("No image data to save")
                return False
            
            # Decode base64
            image_bytes = base64.b64decode(image_data)
            
            image = Image.open(BytesIO(image_bytes))
            image = image.convert('RGB')
            output_path = str(Path(output_path).with_suffix('.jpg'))
            image.save(output_path, 'JPEG', quality=95)
            
            logger.info(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return None


def select_todays_service(service_id: Optional[int] = None) -> Dict:
    """
    Select which service to advertise today.
    Can be called with a specific ID or rotates through services.
    
    Args:
        service_id: Optional specific service ID (1-6)
    
    Returns:
        Service dictionary
    """
    if service_id is None:
        # Rotate through services based on current day
        from datetime import datetime
        day_of_month = datetime.now().day
        # Use day modulo number of services, but ensure we don't always get the last one
        service_id = (day_of_month - 1) % len(SERVICES) + 1
    
    for service in SERVICES:
        if service["id"] == service_id:
            return service
    
    # Default to first service if not found
    return SERVICES[0]


# Example usage functions
if __name__ == "__main__":
    import os
    from config import REFERENCE_IMAGE_PATH
    
    # Initialize client
    client = OpenRouterClient(OPENROUTER_API_KEY)
    
    # Select today's service
    today_service = select_todays_service()
    logger.info(f"Today's service: {today_service['title']}")
    
    # Check if reference image exists
    if not os.path.exists(REFERENCE_IMAGE_PATH):
        logger.warning(f"Reference image not found at {REFERENCE_IMAGE_PATH}")
        logger.info("Please add a reference advertisement image to the project root")
    
    # Generate image prompt
    image_prompt = get_image_prompt(today_service)
    logger.info(f"Image prompt generated ({len(image_prompt)} characters)")
    
    # Generate caption prompt
    caption_prompt = get_caption_prompt(today_service)
    logger.info(f"Caption prompt generated ({len(caption_prompt)} characters)")
    
    logger.info("Client initialized successfully!")
