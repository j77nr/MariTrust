from django.db.models import Case, IntegerField, Prefetch, Value, When
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from declarations.models import Declaration, DeclarationPortEscale


class EspaceDeclarant(RoleRequiredMixin, TemplateView):
    roles = ["declarant"]
    template_name = "dashboard/declarant.html"


class EspaceAgent(RoleRequiredMixin, TemplateView):
    roles = ["agent", "admin"]
    template_name = "dashboard/agent.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        declarations = list(
            Declaration.objects.select_related("navire", "operateur", "declarant")
            .prefetch_related(
                Prefetch(
                    "declarationportescale_set",
                    queryset=DeclarationPortEscale.objects.select_related("port_escale").order_by(
                        "ordre_passage"
                    ),
                    to_attr="escales_ordonnees",
                ),
                "score_details__critere",
            )
            .annotate(
                ordre_risque=Case(
                    When(niveau_risque=Declaration.NiveauRisque.ELEVE, then=Value(0)),
                    When(niveau_risque=Declaration.NiveauRisque.MOYEN, then=Value(1)),
                    default=Value(2),
                    output_field=IntegerField(),
                )
            )
            .order_by("ordre_risque", "-score", "-date_declaration")
        )
        selected_id = self.request.GET.get("declaration")
        selected = next((item for item in declarations if str(item.pk) == selected_id), None)

        context.update(
            declarations=declarations,
            selected_declaration=selected or (declarations[0] if declarations else None),
            declarations_a_traiter=sum(
                item.statut_traitement != Declaration.StatutTraitement.TRAITE
                for item in declarations
            ),
            risques_eleves=sum(
                item.niveau_risque == Declaration.NiveauRisque.ELEVE
                for item in declarations
            ),
        )
        return context


class EspaceAdmin(RoleRequiredMixin, TemplateView):
    roles = ["admin"]
    template_name = "dashboard/admin.html"
