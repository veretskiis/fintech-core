from django.urls import path

from apps.transactions.views import TransferView

app_name = "transactions"
urlpatterns = [
    path("transfer/", TransferView.as_view(), name="transfer"),
]
