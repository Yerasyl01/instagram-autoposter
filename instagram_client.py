import os
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientNotFoundError, ClientError, MediaNotFound, ChallengeRequired

logger = logging.getLogger(__name__)

class InstagramClient(Client):
    def expose(self):
        try:
            return super().expose()
        except ClientNotFoundError as e:
            # Instagram currently returns 404 for qe/expose/.
            # This endpoint is not required to configure the media.
            logger.warning(
                "Instagram qe/expose/ returned 404; "
                "ignoring optional expose request."
            )
            return None

class InstagramPoster:
    """
    Client for posting to Instagram using instagrapi.
    Handles authentication, upload, and publishing of posts.
    """

    def __init__(self, username: str):
        self.username = username
        self.client = InstagramClient()
        self.logged_in = False
        self.session_file = Path(__file__).resolve().parent / "session.json"

    def load_session(self) -> bool:
        """Load and validate the saved Instagram session."""
        try:
            session_path = Path(self.session_file)
            if not session_path.exists():
                logger.info("Instagram session file not found: %s", session_path)
                return False
            logger.info("Loading existing Instagram session...")
            self.client.load_settings(session_path)
            account = self.client.account_info()
            self.logged_in = True
            logger.info(
                "Authenticated as @%s (ID: %s)",
                account.username,
                account.pk,
            )
            self.client.dump_settings(session_path)
            return True

        except LoginRequired:
            self.logged_in = False
            logger.error("Saved Instagram session is no longer valid")
            return False

        except ChallengeRequired as e:
            self.logged_in = False
            logger.error("Instagram requires verification: %s", e)
            return False

        except ClientError as e:
            self.logged_in = False
            logger.error("Instagram client error: %s", e)
            logger.debug("last_json: %s", self.client.last_json)
            return False

        except Exception:
            self.logged_in = False
            logger.exception("Unexpected error while authenticating")
            return False

    def create_session(self) -> bool:
        """Create a new Instagram session from SESSION_ID and save it."""
        try:
            session_id = os.environ.get("SESSION_ID")
            if not session_id:
                logger.error("SESSION_ID is not configured")
                return False
            logger.info("Creating new Instagram session...")
            self.client.login_by_sessionid(session_id)
            account = self.client.account_info()
            self.logged_in = True
            logger.info(
                "Authenticated as @%s (ID: %s)",
                account.username,
                account.pk,
            )
            session_path = Path(self.session_file)
            self.client.dump_settings(session_path)
            logger.info("Instagram session saved to: %s", session_path)
            return True

        except LoginRequired:
            self.logged_in = False
            logger.error("SESSION_ID is no longer valid")
            return False

        except ChallengeRequired as e:
            self.logged_in = False
            logger.error("Instagram requires verification: %s", e)
            return False

        except ClientError as e:
            self.logged_in = False
            logger.error("Instagram client error: %s", e)
            logger.debug("last_json: %s", self.client.last_json)
            return False

        except Exception:
            self.logged_in = False
            logger.exception("Unexpected error while creating Instagram session")
            return False

    def login(self) -> bool:
        """Authenticate using the saved session or create a new one."""
        if self.load_session():
            return True
        logger.info("Saved session unavailable, creating a new session...")
        return self.create_session()

    def logout(self, delete_session=False):
        """Explicitly log out and optionally remove the persisted session."""
        try:
            if self.logged_in:
                self.client.logout()
                self.logged_in = False
                logger.info("Logged out successfully")
            if delete_session:
                session_path = Path(self.session_file)
                if session_path.exists():
                    session_path.unlink()
                    logger.info("Session file removed")
        except Exception as e:
            logger.error("Error during logout: %s", e)

    def upload_post(
        self,
        image_path: str,
        caption: str,
        hashtags: Optional[str] = None
    ):
        """
        Upload and publish a post to Instagram.
        
        Args:
            image_path: Path to the image file
            caption: Post caption without hashtags
            hashtags: Optional hashtags to append
            location: Optional location string
            hashtags: Optional hashtags to append (alternative to in caption)
        
        Returns:
            Media ID if successful, None otherwise
        """
        if not self.logged_in:
            logger.error("Not logged in. Call login() first.")
            return None

        if not Path(image_path).exists():
            logger.error(f"Image file not found: {image_path}")
            return None

        try:
            # Prepare caption
            final_caption = caption
            if hashtags:
                final_caption = f"{caption}\n\n{hashtags}"

            # Upload photo
            logger.info(f"Uploading photo: {image_path}")
            media = self.client.photo_upload(
                path=Path(image_path),
                caption=final_caption
            )

            logger.info(f"Post uploaded. Media ID: {media.id}")
            return media

        except MediaNotFound as e:
            logger.error(f"Media not found error: {str(e)}")
            return None
        except ClientError as e:
            logger.exception(f"Client error during upload")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            return None

    def upload_with_hashtags(
        self,
        image_path: str,
        caption: str,
        custom_hashtags: Optional[list] = None
    ):
        """
        Upload post with automatically generated hashtags.
        
        Args:
            image_path: Path to the image file
            caption: Post caption (without hashtags)
            custom_hashtags: Additional hashtags to include
        
        Returns:
            Media ID if successful, None otherwise
        """
        # Default hashtags for bookkeeping/business in Kazakhstan
        default_hashtags = [
            "#бухгалтерия",
            "#учет",
            "#бизнес",
            "#Казахстан",
            "#Алматы",
            "#делопроизводство",
            "#налоги",
            "#регистрация",
            "#ТОО",
            "#ИП",
            "#eGov"
        ]

        all_hashtags = default_hashtags + (custom_hashtags or [])
        hashtag_str = "\n\n" + " ".join(all_hashtags)

        return self.upload_post(image_path, caption, hashtags=hashtag_str)

    def check_todays_posts(self, username: str) -> list:
        """
        Check if a post was already made today.
        
        Returns:
            List of posts made today
        """
        try:
            user_id = self.client.user_id_from_username(username)
            # Get recent posts (last 10)
            media = self.client.user_medias(user_id, amount=10)
            
            today = datetime.now().date()
            todays_posts = []
            
            for post in media:
                post_time = post.taken_at.date()
                if post_time == today:
                    todays_posts.append(post)
            
            return todays_posts

        except Exception as e:
            logger.error(f"Error checking today's posts: {str(e)}")
            return []


# Convenience function for testing
def test_instagram_connection():
    """Test Instagram login with credentials from config."""
    from config import INSTAGRAM_USERNAME
    
    poster = InstagramPoster(INSTAGRAM_USERNAME)
    
    if poster.login():
        logger.info("Login in Instagram successfully!")
        
        # Check recent posts
        posts = poster.check_todays_posts(INSTAGRAM_USERNAME)
        logger.info(f"Posts made today: {len(posts)}")
        
        poster.logout()
        return True
    else:
        logger.error("Login failed!")
        return False


if __name__ == "__main__":
    test_instagram_connection()
