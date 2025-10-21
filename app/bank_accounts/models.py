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
    image_deposit = models.ImageField(
        upload_to='transactions/deposits/',
        null=True,
        blank=True,
        verbose_name=_("Изображение при пополнении")
    )
    image_withdraw = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_("Изображение при списании")
    )

    cardholder_name = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        default='',
        verbose_name=_("Инициатор операции")
    )
    to_user = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        default='',
        verbose_name=_("Получатель")
    )
    bank = models.CharField(
        max_length=16,
        choices=(
            ("mono", "Monobank"),
            ("privat", "PrivatBank"),
            ("oschad", "Oschadbank"),
            ("raiff", "Raiffeisen Bank"),
            ("pumb", "PUMB"),
            ("abank", "A-Bank"),
            ("izibank", "Izibank"),
            ("sense", "Sense Bank"),
            ("ukrsib", "Ukrsibbank"),
            ("others", "Другой"),
        ),
        default='mono',
        verbose_name=_("Банк")
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
        choices=(
            ("deposit", _("Пополнение")),
            ("withdraw", _("Списание")),
            ("external", _("Внешняя операция")),
        ),
        editable=False,
        verbose_name=_("Тип операции")
    )
    balance_after = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Баланс после транзакции")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Дата и время")
    )
    comment = models.TextField(
        null=True,
        blank=True,
        default='',
        verbose_name=_("Комментарий")
    )

    class Meta:
        verbose_name = _("Транзакция")
        verbose_name_plural = _("Транзакции")

    def save(self, *args, **kwargs):
        if CardAccountModel.objects.filter(card_number=self.to_card).exists():
            self.operation_type = "deposit"
            card = CardAccountModel.objects.get(card_number=self.to_card)
            self.balance_after = card.balance
        elif CardAccountModel.objects.filter(card_number=self.from_card).exists():
            self.operation_type = "withdraw"
            card = CardAccountModel.objects.get(card_number=self.from_card)
            self.balance_after = card.balance
        else:
            self.operation_type = "external"
            self.balance_after = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Транзакция {self.id}: {self.amount} ({self.get_operation_type_display()})"
