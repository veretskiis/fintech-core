import dataclasses
from decimal import Decimal

from apps.transactions.models import Transfer, Wallet


@dataclasses.dataclass
class TransferCreateCommand:
    from_wallet: Wallet
    to_wallet: Wallet
    amount: Decimal
    idempotency_key: str = None

    def __post_init__(self):
        if self.from_wallet.id == self.to_wallet.id:
            raise ValueError("Нельзя отправить на тот же самый кошелёк")

        if self.amount <= Decimal("0.00"):
            raise ValueError("Сумма должна быть больше 0.00")


@dataclasses.dataclass
class TransferResponse:
    transfer: Transfer
