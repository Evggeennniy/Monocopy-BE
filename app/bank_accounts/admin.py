from django.contrib import admin
from bank_accounts.forms import TransactionAdminForm
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
    form = TransactionAdminForm

    list_display = ("id", "operation_type", "to_card", "amount", "balance_after", "timestamp")
    readonly_fields = ("timestamp", "operation_type", "balance_after")
    search_fields = ("from_card", "to_card")
    exclude = ("image_withdraw", "from_card", "to_user")

    def render_change_form(self, request, context, *args, **kwargs):
        """
        Чтобы форма корректно вставляла datalist под поля.
        """
        form = context.get("adminform").form
        if hasattr(form, "as_p_with_datalist"):
            context["adminform"].form = form
            context["adminform"].form.as_p = form.as_p_with_datalist
        return super().render_change_form(request, context, *args, **kwargs)

    def save_model(self, request, obj, form, change):
        """
        При создании новой транзакции обновляем баланс нужной карты.
        """
        if not change:  # только при создании новой транзакции
            if obj.amount <= 0:
                raise ValidationError("Сумма должна быть больше 0.")

            # если нашли карту получателя → пополнение
            to_card = CardAccountModel.objects.filter(card_number=obj.to_card).first()
            from_card = CardAccountModel.objects.filter(card_number=obj.from_card).first()

            if to_card and not from_card:
                obj.operation_type = "deposit"
                to_card.balance += obj.amount
                to_card.save()

            elif from_card and not to_card:
                if from_card.balance < obj.amount:
                    raise ValidationError("Недостаточно средств для списания.")
                obj.operation_type = "withdraw"
                from_card.balance -= obj.amount
                from_card.save()

            elif from_card and to_card:
                # внутренний перевод между своими картами
                if from_card.balance < obj.amount:
                    raise ValidationError("Недостаточно средств на карте отправителя.")
                obj.operation_type = "external"  # можно переименовать в "transfer"
                from_card.balance -= obj.amount
                to_card.balance += obj.amount
                from_card.save()
                to_card.save()
            else:
                # если обе карты неизвестны системе
                obj.operation_type = "external"

        super().save_model(request, obj, form, change)
