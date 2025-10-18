# forms.py
from django import forms
from django.utils.safestring import mark_safe
from bank_accounts.models import TransactionModel, CardAccountModel


class CardNumberDatalistWidget(forms.TextInput):
    """
    Рендерит <input> + <datalist> внутри одного виджета.
    Никакой обязательной связи с БД: поле остаётся CharField (ввод вручную разрешён).
    """

    def __init__(self, queryset=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.qs = queryset or CardAccountModel.objects.none()

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        list_id = attrs.get("list") or f"{name}_datalist"
        attrs["list"] = list_id  # связываем <input list="..."> с <datalist id="...">
        input_html = super().render(name, value, attrs, renderer)

        # Ограничим, например, до 1000 карт, чтобы не раздуть страницу
        options = []
        for c in self.qs[:1000]:
            # Показываем номер + владельца + баланс (можешь изменить формат)
            options.append(
                f'<option value="{c.card_number}">{c.user.username} (₴{c.balance})</option>'
            )
        datalist_html = f'<datalist id="{list_id}">{"".join(options)}</datalist>'
        return mark_safe(input_html + datalist_html)


class TransactionAdminForm(forms.ModelForm):
    # Важно: оставляем CharField, чтобы можно было ввести ЛЮБОЕ значение
    to_card = forms.CharField(required=False, label="Карта получателя")

    class Meta:
        model = TransactionModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cards_qs = CardAccountModel.objects.select_related("user").all()

        self.fields["to_card"].widget = CardNumberDatalistWidget(queryset=cards_qs, attrs={"class": "vTextField"})
