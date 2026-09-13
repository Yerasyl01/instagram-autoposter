import os
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

# API Keys
OPENROUTER_API_KEY = os.environ['OPENROUTER_API_KEY']
# Instagram credentials for posting
INSTAGRAM_USERNAME = "ainagul_batyrgaliyevna"

# Company Information
COMPANY_NAME = "BUSINESS УЧЕТ.KZ"
COMPANY_PHONE = "+7 701 533 44 38"
COMPANY_ADDRESS = "ул. Желтоксан, 103"
CONTACT_INFO = f"""📞 WhatsApp: {COMPANY_PHONE}
📍 {COMPANY_ADDRESS}"""

# Reference image path for brand consistency
REFERENCE_IMAGE_PATH = "reference_ad.jpg"  # Upload this to project root

# List of bookkeeping services with pre-defined prompts
SERVICES = [
    {
        "id": 1,
        "title": "Бухгалтерское сопровождение вашего бизнеса",
        "message": "Передайте бухгалтерский учет профессионалам",
        "prompt_type": "single-service"
    },
    {
        "id": 2,
        "title": "Внутренний аудит и восстановление бухгалтерского учета",
        "message": "Найдём ошибки и восстановим порядок в учете",
        "prompt_type": "single-service"
    },
    {
        "id": 3,
        "title": "Регистрация и ликвидация ТОО и ИП",
        "message": "Поможем оформить бизнес правильно",
        "prompt_type": "single-service"
    },
    {
        "id": 4,
        "title": "Решение налоговых проблем",
        "message": "Разберёмся со сложными налоговыми вопросами",
        "prompt_type": "single-service"
    },
    {
        "id": 5,
        "title": "Помощь в получении РВП и бизнес-виз C3, C5",
        "message": "Помогаем получить разрешения на работу и бизнес",
        "prompt_type": "single-service"
    },
    {
        "id": 6,
        "title": "Бухгалтерская и налоговая консультация для вашего бизнеса",
        "message": "Полный спектр услуг для операционного бизнеса",
        "prompt_type": "general-company"
    }
]

# All services for secondary text in general ads
ALL_SERVICES = [
    "Бухгалтерское сопровождение",
    "Внутренний аудит и восстановление бухгалтерского учета",
    "Решение налоговых проблем",
    "Регистрация и ликвидация ТОО и ИП",
    "РВП и бизнес-визы C3, C5"
]


def get_image_prompt(service: Dict) -> str:
    """
    Build image generation prompt for Meta Muse.
    Uses fixed template with service-specific variables.
    """
    secondary_services_text = f"""
The advertisement should also include these company services:
{chr(10).join(f'- {s}' for s in ALL_SERVICES)}
"""

    prompt = f"""Use the provided reference image as the primary reference for the brand's visual identity and advertising concept.

Create a new, original Instagram advertisement for the bookkeeping and business services company {COMPANY_NAME}.

Maintain the same overall visual language as the reference image:
- clean, premium, professional corporate design
- light white and soft gray background
- subtle blue-gray corporate accents
- spacious and elegant composition
- large strong serif headline on the left side
- clear information hierarchy
- minimal modern outline icons where appropriate
- professional office or business environment
- trustworthy and approachable atmosphere
- a professional person or business-related visual element
- brand logo/name positioned naturally in the upper area

Do not copy the reference image literally.
Create a new original composition while preserving the same design principles, branding feeling, visual hierarchy, and corporate style.

PRIMARY ADVERTISEMENT TOPIC:
{service['title']}

MAIN HEADLINE:
{service['title']}

MAIN DESCRIPTION:
{service['message']}
{secondary_services_text}

CONTACT INFORMATION:
WhatsApp: {COMPANY_PHONE}
{COMPANY_ADDRESS}

CALL TO ACTION:
Напишите нам
Получите бесплатную консультацию

Optimize the design for an Instagram advertisement.

Important:
The main service must be immediately understandable at a glance.
Do not overcrowd the design.
Keep secondary services visually smaller than the main message.
Maintain clear typography, generous spacing, and strong readability.
The final image should look like part of the same advertising campaign as the reference image, but should be a new and distinct advertisement."""

    return prompt


def get_caption_prompt(service: Dict) -> str:
    """
    Build caption generation prompt for Ling 3.0 Flash Fin.
    """
    services_list = "\n".join(f"- {s}" for s in ALL_SERVICES)

    prompt = f"""Create an Instagram caption in Russian for {COMPANY_NAME}.

Service being advertised:
{service['title']}

Main message:
{service['message']}

Company services:
{services_list}

Write a professional but approachable Instagram caption.
Include a call to action.
Do not make unsupported promises.
Do not include hashtags.

Format the caption as plain text ready for Instagram posting with appropriate line breaks and emojis if natural."""

    return prompt
