from django import forms

from public.models import Booking


class BookingForm(forms.ModelForm):
    """Форма заявки на обратный звонок."""

    class Meta:
        model = Booking
        fields = ["name", "phone"]
        widgets = {
            "name": forms.TextInput(attrs={
                "placeholder": "Как к вам обращаться",
                "autocomplete": "name",
            }),
            "phone": forms.TextInput(attrs={
                "placeholder": "+7 (___) ___-__-__",
                "autocomplete": "tel",
                "inputmode": "tel",
            }),
        }

    def clean_name(self):
        """Убираем лишние пробелы и требуем минимум 2 символа."""
        value = self.cleaned_data["name"].strip()
        if len(value) < 2:
            raise forms.ValidationError("Укажите имя (минимум 2 символа).")
        return value
