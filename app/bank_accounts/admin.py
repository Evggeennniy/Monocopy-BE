from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from bank_accounts.models import CardAccountModel, TransactionModel

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")


@admin.register(CardAccountModel)
class CardAccountAdmin(admin.ModelAdmin):
    list_display = ("card_number", "balance", "expiration_date")
    search_fields = ("card_number",)
    list_filter = ("expiration_date",)

    fieldsets = (
        ("Владелец", {
            "fields": ("user",),
        }),
        ("Данные карты", {
            "fields": ("card_number", "expiration_date", "cvv"),
        }),
        ("Финансы", {
            "fields": ("balance",),
        }),
    )


@admin.register(TransactionModel)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "amount", "from_card", "to_card", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("from_card", "to_card",)

    readonly_fields = ("timestamp",)

    def save_model(self, request, obj, form, change):
        if not change:
            if obj.amount <= 0:
                raise ValidationError("Amount must be greater than 0.")

            card = CardAccountModel.objects.filter(card_number=obj.to_card).first()
            if card:
                if obj.operation_type == "deposit":
                    card.balance += obj.amount
                elif obj.operation_type == "withdraw":
                    if card.balance < obj.amount:
                        raise ValidationError("Insufficient funds for withdrawal.")
                    card.balance -= obj.amount
                card.save()

        super().save_model(request, obj, form, change)
