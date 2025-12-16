from rest_framework import generics
from rest_framework.exceptions import ValidationError

from apps.transactions.models import Transfer
from apps.transactions.serializers import TransferSerializer


class TransferView(generics.CreateAPIView):
    serializer_class = TransferSerializer
    queryset = Transfer.objects.all()
    permission_classes = (
        # Отключено из-за отсутствия реализации аутентификации
        # permissions.IsAuthenticated,
        # IsOwnerOfSourceWallet,
    )

    def get_serializer_context(self):
        idempotency_key = self.request.headers.get("Idempotency-Key")
        if not idempotency_key:
            if idempotency_key is None:
                raise ValidationError("Не передан заголовок Idempotency-Key")

            raise ValidationError("Пустой заголовок Idempotency-Key")

        context = super().get_serializer_context()
        context["idempotency_key"] = idempotency_key
        return context
