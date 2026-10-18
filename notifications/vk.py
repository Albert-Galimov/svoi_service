"""Отправка уведомлений ВКонтакте."""

import logging
import random

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

VK_API_VERSION = "5.199"
VK_API_URL = "https://api.vk.com/method/messages.send"
REQUEST_TIMEOUT = 10


def send_message(text: str, user_id: int) -> bool:
    """Отправляет личное сообщение пользователю от имени сообщества.

    Args:
        text: Текст сообщения.
        user_id: ID пользователя-получателя (для личных сообщений
                 совпадает с peer_id).

    Returns:
        True, если сообщение отправлено, иначе False.
    """
    token = settings.VK_GROUP_TOKEN
    if not token:
        logger.warning("VK_GROUP_TOKEN не задан. Уведомление не отправлено.")
        return False

    random_id = random.randint(-2_147_483_648, 2_147_483_647)

    params = {
        "access_token": token,
        "v": VK_API_VERSION,
        "user_id": user_id,
        "message": text,
        "random_id": random_id,
    }

    try:
        response = requests.post(VK_API_URL, params=params, timeout=REQUEST_TIMEOUT)
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error("VK: ошибка сети или разбора ответа: %s", exc)
        return False

    if "error" in data:
        error = data["error"]
        logger.error(
            "VK: ошибка API. code=%s, msg=%s",
            error.get("error_code"),
            error.get("error_msg"),
        )
        return False

    return True
