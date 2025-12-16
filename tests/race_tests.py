import random
import uuid
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal

import pytest
import requests
from django.urls import reverse

from apps.transactions.models import WalletBalance, Transfer, Transaction


@pytest.mark.django_db(transaction=True)
def test_transfer_race_100_requests_same_idempotency(live_server, wallets, balances):
    """
    100 параллельных запросов с одинаковым Idempotency-Key и одинаковым payload.
    """
    from_wallet, to_wallet = wallets
    from_balance, to_balance, admin_balance = balances

    url = live_server.url + reverse("transactions:transfer")
    amount = "1001.00"

    total_before = (
        WalletBalance.objects.get(pk=from_balance.pk).balance
        + WalletBalance.objects.get(pk=to_balance.pk).balance
        + WalletBalance.objects.get(pk=admin_balance.pk).balance
    )
    idem = str(uuid.uuid4())

    def do_request(i: int):
        payload = {
            "from_wallet": str(from_wallet.id),
            "to_wallet": str(to_wallet.id),
            "amount": amount,
        }

        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idem,
        }

        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return i, r.status_code, r.text

    results = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(do_request, i) for i in range(100)]
        for f in as_completed(futures):
            results.append(f.result())

    for i, code, text in sorted(results):
        print(i, code, text)

    assert Transfer.objects.count() == 1

    from_balance.refresh_from_db()
    to_balance.refresh_from_db()
    admin_balance.refresh_from_db()

    assert to_balance.balance == Decimal("10.00") + Decimal(amount)

    total_after = from_balance.balance + to_balance.balance + admin_balance.balance
    assert total_after == total_before
    assert 1 <= Transaction.objects.count() <= 3
    ok = [r for r in results if r[1] in (200, 201)]
    assert len(ok) >= 1


@pytest.mark.django_db(transaction=True)
def test_transfer_race_100_requests_different_idempotency(live_server, wallets, balances, set_balance):
    """
    100 параллельных запросов с разным Idempotency-Key и одинаковым payload.
    """
    from_wallet, to_wallet = wallets
    from_balance, to_balance, admin_balance = balances
    set_balance(from_balance, "5000.00")

    url = live_server.url + reverse("transactions:transfer")
    amount = "1001.00"

    total_before = (
        WalletBalance.objects.get(pk=from_balance.pk).balance
        + WalletBalance.objects.get(pk=to_balance.pk).balance
        + WalletBalance.objects.get(pk=admin_balance.pk).balance
    )

    def do_request(i: int):
        payload = {
            "from_wallet": str(from_wallet.id),
            "to_wallet": str(to_wallet.id),
            "amount": amount,
        }
        idem = str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idem,
        }

        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return i, r.status_code, r.text

    results = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(do_request, i) for i in range(100)]
        for f in as_completed(futures):
            results.append(f.result())

    for i, code, text in sorted(results):
        print(i, code, text)

    assert Transfer.objects.count() == 4

    from_balance.refresh_from_db()
    to_balance.refresh_from_db()
    admin_balance.refresh_from_db()

    assert to_balance.balance == Decimal("10.00") + Decimal(amount) * 4

    total_after = from_balance.balance + to_balance.balance + admin_balance.balance
    assert total_after == total_before
    assert Transaction.objects.exists()
    ok = [r for r in results if r[1] in (200, 201)]
    assert len(ok) >= 1


@pytest.mark.django_db(transaction=True)
def test_transfer_race_100_requests_same_idempotency(live_server, wallets, balances):
    """
    100 параллельных запросов с одинаковым Idempotency-Key и разным payload.
    """
    from_wallet, to_wallet = wallets
    from_balance, to_balance, admin_balance = balances

    url = live_server.url + reverse("transactions:transfer")
    amount = 1001

    total_before = (
        WalletBalance.objects.get(pk=from_balance.pk).balance
        + WalletBalance.objects.get(pk=to_balance.pk).balance
        + WalletBalance.objects.get(pk=admin_balance.pk).balance
    )
    idem = str(uuid.uuid4())

    def do_request(i: int):
        payload = {
            "from_wallet": str(from_wallet.id),
            "to_wallet": str(to_wallet.id),
            "amount": str(amount + random.randint(1, 100)),
        }

        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": idem,
        }

        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=10)
        return i, r.status_code, r.text

    results = []
    with ThreadPoolExecutor(max_workers=50) as ex:
        futures = [ex.submit(do_request, i) for i in range(100)]
        for f in as_completed(futures):
            results.append(f.result())

    for i, code, text in sorted(results):
        print(i, code, text)

    assert Transfer.objects.count() == 1

    from_balance.refresh_from_db()
    to_balance.refresh_from_db()
    admin_balance.refresh_from_db()

    total_after = from_balance.balance + to_balance.balance + admin_balance.balance
    assert total_after == total_before
    ok = [r for r in results if r[1] in (200, 201)]
    assert len(ok) >= 1
