from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied

from apps.transactions.dto import TransferCreateCommand
from apps.transactions.exceptions import (
    NotEnoughMineralsException,
    RaceConditionException,
    ConflictError,
    AdminWalletException,
)
from apps.transactions.models import Transfer, Wallet
from apps.transactions.services import transfer_funds
from apps.transactions.tasks import notify_recipient


class TransferSerializer(serializers.ModelSerializer):

    from_wallet = serializers.PrimaryKeyRelatedField(queryset=Wallet.objects.all(), write_only=True)
    to_wallet = serializers.PrimaryKeyRelatedField(queryset=Wallet.objects.all(), write_only=True)

    def create(self, validated_data):
        try:
            transfer_command = TransferCreateCommand(
                from_wallet=validated_data["from_wallet"],
                to_wallet=validated_data["to_wallet"],
                amount=validated_data["amount"],
                idempotency_key=self.context["idempotency_key"],
            )
        except ValueError as exception:
            raise ValidationError(detail=exception) from exception

        try:
            transfer = transfer_funds(transfer_command).transfer
        except AdminWalletException as exception:
            raise PermissionDenied(detail=exception) from exception
        except NotEnoughMineralsException as exception:
            raise ValidationError(detail=exception) from exception
        except RaceConditionException as exception:
            raise ConflictError(detail=exception) from exception
        else:
            notify_recipient.delay(transfer_id=transfer.id)
            return transfer

    class Meta:
        model = Transfer

        fields = [
            "id",
            "from_wallet",
            "to_wallet",
            "amount",
        ]
        write_only_fields = ["amount"]
        read_only_fields = ["id"]
