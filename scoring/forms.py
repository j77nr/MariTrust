from django import forms
from django.forms import modelformset_factory

from .models import Critere


class CritereAdminForm(forms.ModelForm):
    poids = forms.IntegerField(
        min_value=0,
        max_value=100,
        label="Poids",
        widget=forms.NumberInput(
            attrs={"class": "form-control form-control-sm mt-weight-input", "min": 0, "max": 100}
        ),
    )
    actif = forms.BooleanField(
        required=False,
        label="Actif",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta:
        model = Critere
        fields = ["poids", "actif"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["poids"].widget.attrs["aria-label"] = f"Poids de {self.instance.nom}"
        self.fields["actif"].widget.attrs["aria-label"] = f"Activer {self.instance.nom}"


CritereAdminFormSet = modelformset_factory(
    Critere,
    form=CritereAdminForm,
    extra=0,
)
