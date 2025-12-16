from django.contrib import admin
from django.forms import BaseInlineFormSet

from apps.transactions.models import Transaction, Transfer, WalletBalance, Wallet


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "transfer", "flow", "created_at")
    search_fields = ("id",)
    autocomplete_fields = ("wallet", "transfer")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("wallet", "transfer")


class LimitedInlineFormSet(BaseInlineFormSet):
    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")[:20]


class TransactionInline(admin.TabularInline):
    formset = LimitedInlineFormSet
    model = Transaction
    can_delete = False
    show_change_link = True
    extra = 0
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("wallet", "transfer")

    def has_change_permission(self, request, obj=...):
        return False


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    inlines = [TransactionInline]
    list_display = ("id", "from_wallet", "to_wallet", "amount", "created_at")
    search_fields = ("id",)
    autocomplete_fields = ("from_wallet", "to_wallet")
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("from_wallet", "to_wallet")


@admin.register(WalletBalance)
class WalletBalanceAdmin(admin.ModelAdmin):
    list_display = ("id", "balance", "wallet", "wallet__user", "created_at")
    search_fields = ("id",)
    autocomplete_fields = ("wallet",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("wallet", "wallet__user")


class WalletBalanceInline(admin.TabularInline):
    model = WalletBalance
    can_delete = False
    show_change_link = True
    extra = 0
    fields = ("balance",)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    inlines = [
        WalletBalanceInline,
        TransactionInline,
    ]
    list_display = ("id", "user", "wallet_balance", "created_at")
    search_fields = ("id",)
    autocomplete_fields = ("user",)
    ordering = ("-created_at",)

    @admin.display(description="Баланс кошелька")
    def wallet_balance(self, obj):
        return obj.walletbalance.balance

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("walletbalance")
