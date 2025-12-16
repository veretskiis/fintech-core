from rest_framework.permissions import BasePermission

from apps.transactions.models import Wallet


class IsOwnerOfSourceWallet(BasePermission):
    message = "Вы не владеете этим кошельком"

    def has_permission(self, request, view):
        from_wallet_id = request.data.get("from_wallet")
        if not from_wallet_id:
            return True

        return Wallet.objects.filter(
            id=from_wallet_id,
            user=request.user,
        ).exists()
