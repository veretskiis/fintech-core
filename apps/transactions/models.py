import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class BaseModel(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено",
    )

    class Meta:
        abstract = True


class Wallet(BaseModel):

    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Пользователь",
    )
    is_admin_wallet = models.BooleanField(
        default=False,
        verbose_name="Админский кошелёк",
    )

    class Meta:
        verbose_name = "Кошелёк"
        verbose_name_plural = "Кошельки"
        constraints = [
            models.UniqueConstraint(
                fields=["is_admin_wallet"],
                condition=models.Q(is_admin_wallet=True),
                name="unique_admin_wallet",
            )
        ]

    def __str__(self):
        return f"Кошелёк {self.user}"


class WalletBalance(BaseModel):

    wallet = models.OneToOneField(
        Wallet,
        on_delete=models.PROTECT,
        verbose_name="Кошелёк",
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Баланс",
    )
    version = models.PositiveIntegerField(
        default=0,
        verbose_name="Версия",
        editable=False,
    )

    class Meta:
        verbose_name = "Баланс кошелька"
        verbose_name_plural = "Баланс кошельков"

    def __str__(self):
        return f"Баланс кошелька {self.wallet}"


class Transfer(BaseModel):

    from_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="from_wallets",
        verbose_name="Списано с кошелька",
    )
    to_wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="to_wallets",
        verbose_name="Зачислено на кошелёк",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
    )
    fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Комиссия",
    )
    idempotency_key = models.CharField(
        max_length=255,
        verbose_name="Ключ",
        editable=False,
    )

    class Meta:
        verbose_name = "Перевод"
        verbose_name_plural = "Переводы"
        constraints = [
            models.UniqueConstraint(
                fields=["from_wallet", "idempotency_key"],
                name="unique_transfer",
            )
        ]

    def __str__(self):
        return f"{str(self.from_wallet_id)[:6]} -> {str(self.to_wallet_id)[:6]}"


class Transaction(BaseModel):

    class Flow(models.TextChoices):
        debit = "debit", "Начисление"
        credit = "credit", "Списание"
        fee = "fee", "Комиссия"

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        verbose_name="Кошелёк",
    )
    transfer = models.ForeignKey(
        Transfer,
        on_delete=models.PROTECT,
        verbose_name="Перевод",
    )

    flow = models.CharField(
        choices=Flow.choices,
        verbose_name="Движение",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
    )

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"

    def __str__(self):
        return f"{str(self.transfer.from_wallet_id)[:6]} -> {str(self.transfer.to_wallet_id)[:6]}"
