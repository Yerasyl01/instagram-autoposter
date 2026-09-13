"""
Instagram Autoposter - Daily advertisement poster for bookkeeping business.

This script:
1. Selects today's service to advertise
2. Generates an Instagram ad image using Meta Muse via OpenRouter
3. Generates an Instagram caption using Ling 3.0 Flash Fin via OpenRouter
4. Posts the image + caption to Instagram using instagrapi

Usage:
    python main.py [--service-id ID] [--test] [--dry-run]
"""

import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import (
    OPENROUTER_API_KEY,
    INSTAGRAM_USERNAME,
    REFERENCE_IMAGE_PATH,
    SERVICES,
    CONTACT_INFO
)
from openrouter_client import (
    OpenRouterClient,
    select_todays_service
)
from instagram_client import InstagramPoster

# Configure logging
log_dir = Path(__file__).resolve().parent / "logs"
log_dir.mkdir(exist_ok=True)
file_handler = TimedRotatingFileHandler(
    log_dir/'autoposter.log',
    when='midnight',
    interval=1,
    backupCount=30,
    encoding='utf-8'
)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_or_create_image(service: dict, image_prompt: str, openrouter: OpenRouterClient, reference_image_path: str, regenerate_image: bool) -> Optional[str]:
    """Get existing image for today or generate a new one."""
    # Check for existing image for today's service
    if (not regenerate_image):
        today_prefix = datetime.now().strftime("%Y%m%d")
        if Path("ads").exists():
            existing_images = list(Path("ads").glob(f"{today_prefix}*_{service['id']}_ad.jpg"))
            if existing_images:
                existing_image = max(existing_images, key=lambda p: p.stat().st_mtime)
                logger.info(f"Reusing existing image: {existing_image}")
                return str(existing_image)
    
    # Generate new image
    logger.info("Generating advertisement image...")
    image_data = openrouter.generate_image_with_muse(
        prompt=image_prompt,
        reference_image_path=reference_image_path
    )
    
    if not image_data:
        logger.error("Failed to generate image")
        return None
    
    # Save image
    ads_dir = Path("ads")
    ads_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = openrouter.save_image(
        image_data,
        str(ads_dir / f"{timestamp}_{service['id']}_ad")
    )
    
    if not image_path:
        logger.error("Failed to save generated image")
        return None
    
    logger.info(f"Image saved to: {image_path}")
    return image_path


def create_daily_post(
    service_id: Optional[int] = None,
    dry_run: bool = False,
    test_mode: bool = False,
    regenerate_image: bool = False
) -> bool:
    """
    Create and post a daily Instagram advertisement.
    
    Args:
        service_id: Optional specific service ID (1-6). If None, auto-selects based on date.
        dry_run: If True, only print what would be done without actually posting
        test_mode: If True, skip actual Instagram posting but generate image/caption
        regenerate_image: If True, regenerate existent image for current day
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info(f"Starting daily post creation at {datetime.now()}")
    
    # Select today's service
    service = select_todays_service(service_id)
    logger.info(f"Selected service: {service['title']}")
    
    # Initialize OpenRouter client
    openrouter = OpenRouterClient(OPENROUTER_API_KEY)
    
    # Generate image prompt
    from openrouter_client import get_image_prompt
    image_prompt = get_image_prompt(service)
    
    # Generate caption prompt
    from openrouter_client import get_caption_prompt
    caption_prompt = get_caption_prompt(service)
    
    logger.info(f"Image prompt length: {len(image_prompt)} characters")
    logger.info(f"Caption prompt length: {len(caption_prompt)} characters")
    
    # Check for reference image
    if not Path(REFERENCE_IMAGE_PATH).exists():
        logger.warning(f"Reference image not found at {REFERENCE_IMAGE_PATH}")
        logger.warning("Image generation may fail without reference image")
    
    if dry_run:
        logger.info("DRY RUN MODE - Skipping actual generation")
        logger.info(f"\n--- Image Prompt ---\n{image_prompt[:500]}...")
        logger.info(f"\n--- Caption Prompt ---\n{caption_prompt}")
        return True

    # Generate image
    image_path = get_or_create_image(service, image_prompt, openrouter, REFERENCE_IMAGE_PATH, regenerate_image)
    if not image_path:
        return False
    
    # Generate caption
    logger.info("Generating Instagram caption...")
    caption = openrouter.generate_caption_with_ling(caption_prompt)
    
    if not caption:
        logger.error("Failed to generate caption")
        return False
    
    logger.info("Caption generated successfully")
    logger.info(f"Caption preview: {caption[:200]}...")
    caption = f"{caption}\n\n{CONTACT_INFO}"
    
    # Post to Instagram
    if test_mode:
        logger.info("TEST MODE - Skipping Instagram posting")
        logger.info(f"Would post image: {image_path}")
        logger.info(f"With caption: {caption}")
        return True
    
    logger.info("Posting to Instagram...")
    poster = InstagramPoster(INSTAGRAM_USERNAME)
    
    if not poster.login():
        logger.error("Failed to login in Instagram")
        return False
    
    # Check if already posted today
    todays_posts = poster.check_todays_posts(INSTAGRAM_USERNAME)
    if todays_posts:
        logger.warning(f"Already posted {len(todays_posts)} time(s) today. Skipping.")
        return True
    
    # Upload post with hashtags
    media = poster.upload_with_hashtags(
        image_path=image_path,
        caption=caption
    )
    
    if media:
        logger.info(f"Successfully posted! Media URL: https://www.instagram.com/p/{media.code}")
        return True
    else:
        logger.error("Failed to post to Instagram")
        return False


def main():
    """Main entry point for the autoposter."""
    parser = argparse.ArgumentParser(
        description="Instagram Autoposter for bookkeeping advertisements"
    )
    parser.add_argument(
        "--service-id",
        type=int,
        choices=range(1, len(SERVICES) + 1),
        help="Specific service ID to advertise (1-6). Default: auto-select based on date."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print prompts without generating or posting (for testing)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Generate image and caption but don't post to Instagram"
    )
    parser.add_argument(
        "--regenerate_image",
        action="store_true",
        help="Regenerate image"
    )
    
    args = parser.parse_args()
    
    success = create_daily_post(
        service_id=args.service_id,
        dry_run=args.dry_run,
        test_mode=args.test,
        regenerate_image=args.regenerate_image
    )
    
    if success:
        logger.info("Post creation completed successfully!")
    else:
        logger.error("Post creation failed!")
    
    return success


if __name__ == "__main__":
    main()
