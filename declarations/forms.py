from django import forms
from django.forms import inlineformset_factory

from .models import Declaration, DeclarationPortEscale


class DeclarationForm(forms.ModelForm):
    """Champs que le déclarant est autorisé à renseigner lui-même."""

    class Meta:
        model = Declaration
        fields = [
            "navire", "type_marchandise", "poids_declare_kg", "type_conteneur",
            "valeur_declaree", "moyen_paiement", "date_arrivee_prevue",
        ]
        widgets = {
            "date_arrivee_prevue": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
        self.fields["navire"].widget.attrs["class"] = "form-select"
        self.fields["moyen_paiement"].widget.attrs["class"] = "form-select"


class DeclarationPortEscaleForm(forms.ModelForm):
    class Meta:
        model = DeclarationPortEscale
        fields = ["port_escale"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["port_escale"].required = False
        self.fields["port_escale"].widget.attrs["class"] = "form-select"


PortEscaleFormSet = inlineformset_factory(
    Declaration,
    DeclarationPortEscale,
    form=DeclarationPortEscaleForm,
    extra=10,
    max_num=10,
    validate_max=True,
    can_delete=False,
)