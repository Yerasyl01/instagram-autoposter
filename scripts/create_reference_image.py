#!/usr/bin/env python3
"""
Create a reference advertisement image to establish brand identity.
This script generates a sample reference image that shows the design style
that should be maintained across all Instagram advertisements.
"""

from openrouter_client import OpenRouterClient, get_image_prompt
from config import OPENROUTER_API_KEY, COMPANY_NAME, SERVICES
from datetime import datetime
from pathlib import Path

# Use first service as reference generation
reference_service = SERVICES[0]

# Create a prompt for the reference image showing the ideal style
reference_prompt = f"""Create a premium Instagram advertisement image for {COMPANY_NAME} bookkeeping services. 

This is a REFERENCE IMAGE to establish the visual style for all future advertisements.

Design requirements:
- Clean, premium corporate design with white and soft gray gradient background
- Blue-gray corporate accent colors
- Large serif headline in the top-left area: "{reference_service['title']}"
- Professional businessperson or accountant with documents/laptop on the right side
- Simple outline icons for services
- Company branding prominently displayed: {COMPANY_NAME}
- Contact information visible but not dominant
- spacious layout with generous whitespace
- Professional, trustworthy, and approachable atmosphere
- Suitable for Instagram portrait format (1080x1350)
- Modern typography with clear information hierarchy
- No actual text to be read, this is purely for visual style reference

Do NOT include specific Russian text, phone numbers, or addresses - this is for visual style only."""

def create_reference_image():
    """Generate the reference advertisement image."""
    print("Creating reference advertisement image...")
    print(f"Company: {COMPANY_NAME}")
    print(f"This will establish the visual style for all future Instagram ads")
    
    # Initialize OpenRouter client
    client = OpenRouterClient(OPENROUTER_API_KEY)
    
    # Generate image
    print("\nGenerating reference image via Meta Muse...")
    image_data = client.generate_image_with_muse(
        prompt=reference_prompt,
        reference_image_path=None,  # No reference needed for first image
        width=1080,
        height=1350
    )
    
    if image_data:
        # Save the image
        output_path = Path(__file__).resolve().parent.parent / "reference_ad.jpg"
        if client.save_image(image_data, str(output_path)):
            print(f"\n✓ Reference image created successfully!")
            print(f"  Saved as: {output_path}")
            print(f"\nIMPORTANT: Review this image carefully.")
            print("All future advertisements should match this visual style.")
            print("\nNext steps:")
            print("1. Review the reference image")
            print("2. If satisfied, run: python main.py --test")
            print("3. If changes needed, modify the script and regenerate")
            return True
    
    print("\n✗ Failed to create reference image")
    return False


if __name__ == "__main__":
    create_reference_image()
