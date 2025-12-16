import logging
import random
import time
from celery import shared_task

from apps.transactions.models import Transfer

logger = logging.getLogger("transactions")
logger.setLevel(logging.DEBUG)


@shared_task(bind=True, default_retry_delay=1, max_retries=3)
def notify_recipient(self, transfer_id: int) -> None:
    transfer = Transfer.objects.get(id=transfer_id)
    logger.debug(
        f"Уведомление для перевода {transfer_id}: {str(transfer.from_wallet.id)[:8]} -> {str(transfer.to_wallet.id)[:8]}"
    )
    time.sleep(5)

    # симуляция падения
    if random.random() < 0.5:
        raise self.retry(exc=RuntimeError("Не удалось отправить уведомление"))

    logger.debug(f"Уведомление для перевода {transfer_id} отправлено")
    return None
