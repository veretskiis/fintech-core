import random
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import F

from apps.transactions.dto import TransferCreateCommand
from apps.transactions.models import Wallet, WalletBalance
from apps.transactions.services import transfer_funds  # <-- твоя функция transfer(cmd)


TWO_PLACES = Decimal("0.01")


def q2(x: Decimal) -> Decimal:
    return x.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = "Seed wallets and random transfer history using existing transfer() service"

    def add_arguments(self, parser):
        parser.add_argument("--wallets", type=int, default=50)
        parser.add_argument("--transfers", type=int, default=3000)  # ~120 tx per wallet avg
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--initial-min", type=str, default="5000.00")
        parser.add_argument("--initial-max", type=str, default="20000.00")
        parser.add_argument("--admin-topup", type=str, default="100000.00")

    def handle(self, *args, **opts):
        random.seed(opts["seed"])

        wallets_count = opts["wallets"]
        transfers_count = opts["transfers"]
        initial_min = Decimal(opts["initial_min"])
        initial_max = Decimal(opts["initial_max"])
        admin_topup = Decimal(opts["admin_topup"])

        User = get_user_model()

        admin_user, _ = User.objects.get_or_create(
            username="admin_wallet_user",
            defaults={"email": "admin-wallet@example.com"},
        )
        admin_wallet, _ = Wallet.objects.get_or_create(
            is_admin_wallet=True,
            defaults={"user": admin_user},
        )
        admin_balance, _ = WalletBalance.objects.get_or_create(
            wallet=admin_wallet,
            defaults={"balance": Decimal("0.00"), "version": 0},
        )

        WalletBalance.objects.filter(wallet=admin_wallet).update(
            balance=F("balance") + admin_topup,
            version=F("version") + 1,
        )

        # 2) обычные кошельки + стартовые балансы
        wallets = list(Wallet.objects.all())
        for i in range(wallets_count):
            username = f"seed_user_{i:03d}"
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.com"},
            )
            w, _ = Wallet.objects.get_or_create(user=user, defaults={"is_admin_wallet": False})
            wb, created = WalletBalance.objects.get_or_create(wallet=w)
            if created:
                wb.balance = q2(Decimal(str(random.uniform(float(initial_min), float(initial_max)))))
                wb.version = 0
                wb.save(update_fields=["balance", "version", "updated_at"])

            wallets.append(w)

        ok = 0
        skipped = 0
        for _ in range(transfers_count):
            from_w = random.choice(wallets)
            to_w = random.choice(wallets)
            if from_w.pk == to_w.pk:
                continue

            amount = q2(Decimal(str(random.uniform(1.0, 2500.0))))
            cmd = TransferCreateCommand(
                from_wallet=from_w,
                to_wallet=to_w,
                amount=amount,
                idempotency_key=str(uuid.uuid4()),
            )

            try:
                transfer_funds(cmd)  # <-- используем твою функцию
                ok += 1
            except Exception as exception:
                print(exception)
                skipped += 1
                continue

        self.stdout.write(self.style.SUCCESS(f"Done. Transfers OK={ok}, skipped={skipped}"))
        self.stdout.write(self.style.SUCCESS(f"Admin wallet id={admin_wallet.pk} (topped up by {admin_topup})"))
