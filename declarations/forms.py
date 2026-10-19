from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

from .models import Declaration, DeclarationPortEscale


def valider_imo(imo):
    """Valide un numéro IMO : 7 chiffres, checksum sur 6 premiers * [7,6,5,4,3,2]."""
    imo = str(imo).strip()
    if len(imo) != 7 or not imo.isdigit():
        raise ValidationError("Le numéro IMO doit contenir exactement 7 chiffres.")
    poids = [7, 6, 5, 4, 3, 2]
    total = sum(int(d) * p for d, p in zip(imo[:6], poids))
    if total % 10 != int(imo[6]):
        raise ValidationError("Numéro IMO invalide (chiffre de contrôle incorrect).")
    return imo


class DeclarationForm(forms.ModelForm):
    """Champs que le déclarant est autorisé à renseigner lui-même."""

    # Saisie libre du navire (remplace le dropdown ModelChoiceField)
    navire_nom = forms.CharField(
        label="Nom du navire", max_length=150,
        help_text="Recherche par IMO. Si le navire n'existe pas, il sera créé."
    )
    navire_imo = forms.CharField(
        label="Numéro IMO", max_length=10,
        help_text="7 chiffres (ex: 9074729)."
    )
    navire_pavillon = forms.CharField(
        label="Pavillon", max_length=100, required=False,
        help_text="Requis seulement si le navire est nouveau."
    )

    class Meta:
        model = Declaration
        fields = [
            "type_marchandise", "poids_declare_kg", "type_conteneur",
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
        self.fields["moyen_paiement"].widget.attrs["class"] = "form-select"

    def clean_navire_imo(self):
        return valider_imo(self.cleaned_data["navire_imo"])


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