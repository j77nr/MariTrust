from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import DeclarationForm, PortEscaleFormSet
from .models import Declaration, Navire


def _verifier_declarant_avec_societe(request):
    """Empêche toute déclaration au nom d'un compte non rattaché."""
    if not request.user.est_declarant:
        raise PermissionDenied("Seuls les déclarants peuvent accéder à cet espace.")
    if request.user.societe_id is None:
        raise PermissionDenied("Votre compte déclarant n'est rattaché à aucune société.")


@login_required
def creer_declaration(request):
    _verifier_declarant_avec_societe(request)
    declaration = Declaration()
    if request.method == "POST":
        form = DeclarationForm(request.POST, instance=declaration)
        formset = PortEscaleFormSet(request.POST, instance=declaration)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # --- Saisie libre du navire : recherche par IMO ou création ---
                navire_imo = form.cleaned_data["navire_imo"]
                navire_nom = form.cleaned_data["navire_nom"]
                navire_pavillon = form.cleaned_data["navire_pavillon"]

                # navire_pavillon est requis seulement si le navire n'existe pas encore.
                # On vérifie l'existence AVANT get_or_create pour éviter la création
                # accidentelle quand le pavillon est manquant.
                if not Navire.objects.filter(numero_imo=navire_imo).exists() and not navire_pavillon:
                    form.add_error(
                        "navire_pavillon",
                        "Le pavillon est requis pour un nouveau navire."
                    )
                    return render(request, "declarations/declaration_form.html", {
                        "form": form, "formset": formset, "societe": request.user.societe,
                    })

                navire, navire_cree = Navire.objects.get_or_create(
                    numero_imo=navire_imo,
                    defaults={"nom": navire_nom, "pavillon_actuel": navire_pavillon or "Inconnu"},
                )
                if not navire_cree:
                    # Le navire existe : on ne modifie JAMAIS ses champs
                    if navire.nom != navire_nom:
                        messages.info(
                            request,
                            f"Navire existant conservé : {navire.nom} (IMO {navire_imo})."
                        )

                declaration = form.save(commit=False)
                # L'opérateur est la société consignataire du compte : le
                # déclarant ne peut jamais déposer au nom d'une autre société.
                declaration.declarant = request.user
                declaration.operateur = request.user.societe
                declaration.navire = navire
                declaration.save()
                for ordre, escale in enumerate(formset.save(commit=False), start=1):
                    escale.declaration = declaration
                    escale.ordre_passage = ordre
                    escale.save()
            return redirect("declarations:mes_declarations")
    else:
        form = DeclarationForm(instance=declaration)
        formset = PortEscaleFormSet(instance=declaration)
    return render(request, "declarations/declaration_form.html", {
        "form": form, "formset": formset, "societe": request.user.societe,
    })


@login_required
def mes_declarations(request):
    _verifier_declarant_avec_societe(request)
    declarations = (
        Declaration.objects.filter(declarant=request.user)
        .select_related("navire", "operateur")
        .prefetch_related("declarationportescale_set__port_escale")
    )
    return render(request, "declarations/declaration_list.html", {"declarations": declarations})