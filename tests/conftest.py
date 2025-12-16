import os

import pytest
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.transactions.models import (
    Wallet,
    WalletBalance,
    Transfer,
    Transaction,
)


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username="user1", password="pass")


@pytest.fixture
def user2(db):
    User = get_user_model()
    return User.objects.create_user(username="user2", password="pass")


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_user(username="admin", password="pass")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def wallets(db, user, user2):
    """
    Возвращает (from_wallet, to_wallet)
    """
    from_wallet = Wallet.objects.create(
        user=user,
        is_admin_wallet=False,
    )
    to_wallet = Wallet.objects.create(
        user=user2,
        is_admin_wallet=False,
    )
    return from_wallet, to_wallet


@pytest.fixture
def admin_wallet(db, admin_user):
    """
    Единственный админский кошелёк (unique constraint).
    """
    return Wallet.objects.create(
        user=admin_user,
        is_admin_wallet=True,
    )


@pytest.fixture
def balances(db, wallets, admin_wallet):
    """
    Балансы:
    - from_wallet: 5000.00
    - to_wallet: 10.00
    - admin_wallet: 0.00
    """
    from_wallet, to_wallet = wallets

    from_balance = WalletBalance.objects.create(
        wallet=from_wallet,
        balance=Decimal("5000.00"),
    )
    to_balance = WalletBalance.objects.create(
        wallet=to_wallet,
        balance=Decimal("10.00"),
    )
    admin_balance = WalletBalance.objects.create(
        wallet=admin_wallet,
        balance=Decimal("0.00"),
    )

    return from_balance, to_balance, admin_balance


@pytest.fixture
def set_balance():
    def _set(balance: WalletBalance, value: str | Decimal):
        balance.balance = Decimal(value)
        balance.save(update_fields=["balance"])
        balance.refresh_from_db()
        return balance

    return _set
