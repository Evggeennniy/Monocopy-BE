from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class CardAccountModel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Пользователь"),
        related_name="card_accounts"
    )
    card_number = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        verbose_name=_("Номер карты")
    )
    expiration_date = models.DateField(verbose_name=_("Срок действия"))
    cvv = models.CharField(max_length=4, verbose_name=_("CVV код"))
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_("Баланс")
    )

    class Meta:
        verbose_name = _("Банковская карта")
        verbose_name_plural = _("Банковские карты")

    def __str__(self):
        return self.card_number


class TransactionModel(models.Model):
    OPERATION_CHOICES = (
        ("deposit", _("Пополнение")),
        ("withdraw", _("Списание")),
        ("external", _("Внешняя операция")),
    )

    cardholder_name = models.CharField(
        max_length=32,
        verbose_name=_("Инициатор операции")
    )
    from_card = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name=_("Карта отправителя")
    )
    to_card = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name=_("Карта получателя")
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Сумма")
    )
    operation_type = models.CharField(
        max_length=10,
        choices=OPERATION_CHOICES,
        editable=False,
        verbose_name=_("Тип операции")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата и время")
    )

    class Meta:
        verbose_name = _("Транзакция")
        verbose_name_plural = _("Транзакции")

    def save(self, *args, **kwargs):
        if CardAccountModel.objects.filter(card_number=self.to_card).exists():
            self.operation_type = "deposit"
        elif CardAccountModel.objects.filter(card_number=self.from_card).exists():
            self.operation_type = "withdraw"
        else:
            self.operation_type = "external"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Транзакция {self.id}: {self.amount} ({self.get_operation_type_display()})"
