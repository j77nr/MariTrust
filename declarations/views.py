from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import DeclarationForm, PortEscaleFormSet
from .models import Declaration


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
                declaration = form.save(commit=False)
                # L'opérateur est la société consignataire du compte : le
                # déclarant ne peut jamais déposer au nom d'une autre société.
                declaration.declarant = request.user
                declaration.operateur = request.user.societe
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