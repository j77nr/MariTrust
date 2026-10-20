from datetime import datetime, time, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Case, Count, IntegerField, Prefetch, Value, When
from django.db.models.functions import TruncDate
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.mixins import RoleRequiredMixin
from declarations.models import Declaration, DeclarationPortEscale
from scoring.forms import CritereAdminFormSet
from scoring.models import Critere

Utilisateur = get_user_model()


class EspaceDeclarant(RoleRequiredMixin, TemplateView):
    roles = ["declarant"]
    template_name = "dashboard/declarant.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        declarations = Declaration.objects.filter(declarant=self.request.user).select_related(
            "navire", "operateur"
        )
        context.update(
            declarations_recentes=declarations[:5],
            nombre_declarations=declarations.count(),
            declarations_en_attente=declarations.filter(
                statut_traitement=Declaration.StatutTraitement.EN_ATTENTE
            ).count(),
        )
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        today = timezone.localdate()
        first_day = today - timedelta(days=6)
        week_start = timezone.make_aware(
            datetime.combine(first_day, time.min), timezone.get_current_timezone()
        )
        recent_start = now - timedelta(days=30)

        day_totals = {
            row["jour"]: row["total"]
            for row in Declaration.objects.filter(date_declaration__gte=week_start)
            .annotate(jour=TruncDate("date_declaration", tzinfo=timezone.get_current_timezone()))
            .values("jour")
            .annotate(total=Count("pk"))
        }
        trend = []
        peak = max(day_totals.values(), default=0)
        for offset in range(7):
            day = first_day + timedelta(days=offset)
            total = day_totals.get(day, 0)
            trend.append(
                {
                    "jour": day,
                    "total": total,
                    "hauteur": round(total * 100 / peak) if peak else 0,
                }
            )

        recent_declarations = Declaration.objects.filter(date_declaration__gte=recent_start)
        risk_counts = {
            row["niveau_risque"]: row["total"]
            for row in recent_declarations.values("niveau_risque").annotate(total=Count("pk"))
        }
        risk_total = sum(risk_counts.values())
        risks = [
            {
                "code": code,
                "label": label,
                "total": risk_counts.get(code, 0),
                "pourcentage": round(risk_counts.get(code, 0) * 100 / risk_total)
                if risk_total
                else 0,
            }
            for code, label in Declaration.NiveauRisque.choices
        ]

        users = Utilisateur.objects.order_by("username")
        users_total = users.count()
        users_actifs = users.filter(is_active=True).count()
        context.update(
            declarations_total=Declaration.objects.count(),
            risques_eleves=recent_declarations.filter(
                niveau_risque=Declaration.NiveauRisque.ELEVE
            ).count(),
            declaration_risque_total=risk_total,
            pourcentage_risque_eleve=round(risk_counts.get(Declaration.NiveauRisque.ELEVE, 0) * 100 / risk_total, 1)
            if risk_total
            else 0,
            utilisateurs_total=users_total,
            utilisateurs_actifs=users_actifs,
            utilisateurs=users,
            critere_formset=CritereAdminFormSet(queryset=Critere.objects.all(), prefix="criteres"),
            tendance=trend,
            repartition_risque=risks,
            date_du_jour=today,
        )
        return context

    def post(self, request, *args, **kwargs):
        formset = CritereAdminFormSet(
            request.POST,
            queryset=Critere.objects.all(),
            prefix="criteres",
        )
        if formset.is_valid():
            formset.save()
            messages.success(request, "Les critères de scoring ont été mis à jour.")
            return redirect("espace_admin")

        context = self.get_context_data(**kwargs)
        context["critere_formset"] = formset
        return self.render_to_response(context)
