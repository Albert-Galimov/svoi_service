"""Бизнес-логика уведомлений."""

import logging

from django.conf import settings
from django.utils import timezone

from . import vk

logger = logging.getLogger(__name__)


def _format_booking_vk(booking) -> str:
    """Текст уведомления о заявке для личного сообщения ВК."""
    created_local = timezone.localtime(booking.created_at)
    created_str = created_local.strftime("%d.%m.%Y %H:%M")

    return (
        "🔔 Новая заявка с сайта\n"
        "\n"
        f"👤 {booking.name}\n"
        f"📞 {booking.phone}\n"
        "\n"
        f"🕒 {created_str}"
    )


def notify_about_booking(booking) -> bool:
    """Уведомляет владельца о новой заявке в ВК (личным сообщением)."""
    if not settings.VK_OWNER_ID:
        logger.warning("VK_OWNER_ID не задан — уведомление не отправлено.")
        return False

    text = _format_booking_vk(booking)
    sent = vk.send_message(text, user_id=settings.VK_OWNER_ID)

    if not sent:
        logger.warning(
            "Не удалось отправить уведомление в ВК о заявке id=%s", booking.pk
        )
    return sent
