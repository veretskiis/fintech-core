import logging
import uuid
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.transactions.models import WalletBalance, Transfer, Transaction

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.mark.django_db
def test_transfer_happy_path(api_client, wallets, balances):
    from_wallet, to_wallet = wallets
    from_balance, to_balance, admin_balance = balances

    url = reverse("transactions:transfer")
    amount = Decimal("1001.00")

    response = api_client.post(
        url,
        data={
            "from_wallet": from_wallet.id,
            "to_wallet": to_wallet.id,
            "amount": str(amount),
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert response.status_code in (200, 201), response.content
    logger.info(f"{response.status_code} {response.text}")
    from_balance.refresh_from_db()
    to_balance.refresh_from_db()
    admin_balance.refresh_from_db()

    assert to_balance.balance == Decimal("10.00") + amount
    assert Transfer.objects.count() == 1
    assert Transaction.objects.exists()


@pytest.mark.django_db
def test_transfer_identical_idempotency_key(api_client, wallets, balances):
    from_wallet, to_wallet = wallets
    from_balance, to_balance, admin_balance = balances

    url = reverse("transactions:transfer")
    amount = Decimal("1001.00")

    idempotency_key = str(uuid.uuid4())
    response = api_client.post(
        url,
        data={
            "from_wallet": from_wallet.id,
            "to_wallet": to_wallet.id,
            "amount": str(amount),
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )

    assert response.status_code in (200, 201), response.content
    logger.info(f"{response.status_code} {response.text}")
    transfer_id = response.json()["id"]
    response = api_client.post(
        url,
        data={
            "from_wallet": from_wallet.id,
            "to_wallet": to_wallet.id,
            "amount": str(amount),
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=idempotency_key,
    )

    assert response.status_code in (200, 201), response.content
    logger.info(f"{response.status_code} {response.text}")
    second_transfer_id = response.json()["id"]

    from_balance.refresh_from_db()
    to_balance.refresh_from_db()
    admin_balance.refresh_from_db()

    assert to_balance.balance == Decimal("10.00") + amount
    assert Transfer.objects.count() == 1
    assert Transaction.objects.exists()
    assert transfer_id == second_transfer_id


@pytest.mark.django_db
def test_transfer_not_enough_minerals(api_client, wallets, balances, set_balance):
    from_wallet, to_wallet = wallets
    from_balance, to_balance, admin_balance = balances
    set_balance(from_balance, "1000.00")
    url = reverse("transactions:transfer")
    amount = Decimal("1001.00")

    response = api_client.post(
        url,
        data={
            "from_wallet": from_wallet.id,
            "to_wallet": to_wallet.id,
            "amount": str(amount),
        },
        format="json",
        HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
    )

    assert response.status_code in (400,), response.content
    logger.info(f"{response.status_code} {response.text}")
    before_balance = to_balance.balance
    from_balance.refresh_from_db()
    to_balance.refresh_from_db()
    admin_balance.refresh_from_db()

    assert to_balance.balance == before_balance
    assert Transfer.objects.count() == 0
    assert not Transaction.objects.exists()
