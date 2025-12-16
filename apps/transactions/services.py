import logging
from decimal import Decimal
import uuid

from django.db import transaction as db_transaction, IntegrityError
from django.db.models import F

from .dto import TransferCreateCommand, TransferResponse
from .exceptions import RaceConditionException, NotEnoughMineralsException, AdminWalletException
from .models import Wallet, WalletBalance, Transaction, Transfer

logger = logging.getLogger("transactions")
logger.setLevel(logging.DEBUG)


def transfer_funds(transfer_command: TransferCreateCommand) -> TransferResponse:
    admin_account = Wallet.objects.get(is_admin_wallet=True)

    if admin_account.id in (transfer_command.from_wallet.id, transfer_command.to_wallet.id):
        raise AdminWalletException("Админский кошелёк не может участвовать в переводах")

    if transfer_command.amount > Decimal("1000.00"):
        fee = (transfer_command.amount * Decimal("0.10")).quantize(Decimal("0.01"))
    else:
        fee = Decimal("0.00")

    credit = transfer_command.amount + fee
    idempotency_key = transfer_command.idempotency_key or str(uuid.uuid4())
    with db_transaction.atomic():
        from_balance = WalletBalance.objects.get(wallet=transfer_command.from_wallet)
        to_balance = WalletBalance.objects.get(wallet=transfer_command.to_wallet)
        admin_balance = WalletBalance.objects.get(wallet=admin_account)

        if from_balance.balance < credit:
            raise NotEnoughMineralsException("Недостаточно минералов")

        from_version = from_balance.version
        to_version = to_balance.version
        admin_version = admin_balance.version if admin_balance else None

        try:
            transfer, created = Transfer.objects.get_or_create(
                from_wallet=transfer_command.from_wallet,
                idempotency_key=idempotency_key,
                to_wallet=transfer_command.to_wallet,
                amount=transfer_command.amount,
                fee=fee,
            )
        except IntegrityError as exception:
            # Существующий from_wallet + idempotency_key, но с другими данными
            raise RaceConditionException("Невозможно выполнить перевод (констрейнт)") from exception

        if not created:
            # Если всё один в один, то отдадим существующий перевод
            return TransferResponse(transfer=transfer)

        updated = WalletBalance.objects.filter(
            wallet=transfer_command.from_wallet,
            version=from_version,
            balance__gte=credit,
        ).update(
            balance=F("balance") - credit,
            version=F("version") + 1,
        )

        if updated != 1:
            raise RaceConditionException("Выполняется другая операция (версия)")

        updated = WalletBalance.objects.filter(
            wallet=transfer_command.to_wallet,
            version=to_version,
        ).update(
            balance=F("balance") + transfer_command.amount,
            version=F("version") + 1,
        )

        if updated != 1:
            raise RaceConditionException("Выполняется другая операция (версия)")

        if fee > Decimal("0.00"):
            updated = WalletBalance.objects.filter(
                wallet=admin_account,
                version=admin_version,
            ).update(
                balance=F("balance") + fee,
                version=F("version") + 1,
            )

            if updated != 1:
                raise RaceConditionException("Выполняется другая операция (версия)")

        Transaction.objects.create(
            wallet=transfer_command.from_wallet,
            transfer=transfer,
            flow=Transaction.Flow.credit,
            amount=credit,
        )
        Transaction.objects.create(
            wallet=transfer_command.to_wallet,
            transfer=transfer,
            flow=Transaction.Flow.debit,
            amount=transfer_command.amount,
        )
        if fee > Decimal("0.00"):
            Transaction.objects.create(
                wallet=admin_account,
                transfer=transfer,
                flow=Transaction.Flow.fee,
                amount=fee,
            )

    return TransferResponse(transfer=transfer)
