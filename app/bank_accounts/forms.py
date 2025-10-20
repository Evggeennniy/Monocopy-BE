# forms.py
import re
import os
from django import forms
from django.utils.safestring import mark_safe
from bank_accounts.models import TransactionModel, CardAccountModel
from django.conf import settings
import math
import random

# функция для натуральной сортировки


def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]


class ImageSelectWidget(forms.RadioSelect):
    """
    Виджет для выбора изображений с миниатюрами.
    """

    def render(self, name, value, attrs=None, renderer=None):
        output = ['<div style="display:flex; flex-wrap:wrap; gap:5px;">']
        for opt_value, _ in self.choices:
            if not opt_value:
                continue
            checked = 'checked' if str(value) == str(opt_value) else ''
            output.append(f'''
                <label style="cursor:pointer;">
                    <input type="radio" name="{name}" value="{opt_value}" {checked} style="display:none;">
                    <img src="{opt_value}" width="60" height="60"
                         style="object-fit:cover; border:1px solid #ccc; border-radius:4px; transition:border 0.2s;">
                </label>
            ''')
        output.append('</div>')
        output.append(f"""
        <script>
        (function(){{
            const radios = document.querySelectorAll('input[name="{name}"]');
            function highlight() {{
                radios.forEach(r => r.nextElementSibling.style.border='1px solid #ccc');
                radios.forEach(r => {{
                    if(r.checked) r.nextElementSibling.style.border='2px solid #007bff';
                }});
            }}
            radios.forEach(r => r.addEventListener('change', highlight));
            highlight();
        }})();
        </script>
        """)
        return mark_safe("".join(output))


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


class AnyChoiceField(forms.ChoiceField):
    def validate(self, value):
        # Отключаем стандартную проверку "value in choices"
        return


class TransactionAdminForm(forms.ModelForm):
    to_card = forms.CharField(required=False, label="Карта получателя")
    image_deposit_choice = AnyChoiceField(
        label="Или выберите готовое изображение",
        required=False,
        choices=[],
        widget=ImageSelectWidget,  # виджет с миниатюрами
    )

    class Meta:
        model = TransactionModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []

        # --- datalist для выбора карты ---
        cards_qs = CardAccountModel.objects.select_related("user").all()
        self.fields["to_card"].widget = CardNumberDatalistWidget(
            queryset=cards_qs,
            attrs={"class": "vTextField"},
        )

        # локальные картинки
        samples_path = os.path.join(settings.MEDIA_ROOT, "transaction_imgs")
        if os.path.exists(samples_path):
            files = [f for f in os.listdir(samples_path) if f.lower().endswith((".jpg", ".png", ".jpeg", ".gif"))]
            files.sort(key=natural_sort_key)
            choices.extend([(os.path.join(settings.MEDIA_URL, "transaction_imgs", f), f) for f in files])

        # заголовок
        choices.append(("", "--- Рандомные аватарки ---"))
        self.fields["image_deposit_choice"].choices = choices

    def clean(self):
        cleaned_data = super().clean()
        choice = cleaned_data.get("image_deposit_choice")
        uploaded_file = self.files.get("image_deposit")

        # приоритет — файл
        if uploaded_file:
            cleaned_data["image_deposit"] = uploaded_file
        elif choice:
            # сохраняем как строку (путь)
            cleaned_data["image_deposit"] = choice.strip()
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        image_value = self.cleaned_data.get("image_deposit")

        if isinstance(image_value, str) and image_value:
            relative_path = image_value.replace(settings.MEDIA_URL, "").lstrip("/")
            instance.image_deposit = relative_path
        elif image_value:
            instance.image_deposit = image_value

        if commit:
            instance.save()
        return instance
