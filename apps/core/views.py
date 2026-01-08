from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Avg, F, ExpressionWrapper, fields
from django.db.models.functions import TruncMonth, Coalesce
import json
from django.views.generic import TemplateView

from incidents.models import Incident, Action


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Base querysets
        incidents = Incident.objects.all()
        actions = Action.objects.all()
        
        # Context for dropdowns
        from core.models import Company, Site
        context["companies"] = Company.objects.all().order_by("name")
        context["sites"] = Site.objects.select_related("company").order_by("company__name", "name")

        # If inspector, filter by their visits (optional logic based on your needs)
        if not self.request.user.is_staff:
             incidents = incidents.filter(visit__inspector=self.request.user)
             actions = actions.filter(incident__visit__inspector=self.request.user)

        # Filters
        company = self.request.GET.get("company")
        site = self.request.GET.get("site")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if company:
            incidents = incidents.filter(visit__company__name__icontains=company)
            actions = actions.filter(incident__visit__company__name__icontains=company)
        
        if site:
            incidents = incidents.filter(visit__site__name__icontains=site)
            actions = actions.filter(incident__visit__site__name__icontains=site)

        if date_from:
            incidents = incidents.filter(incident_date__gte=date_from)
            actions = actions.filter(incident__incident_date__gte=date_from)

        if date_to:
            incidents = incidents.filter(incident_date__lte=date_to)
            actions = actions.filter(incident__incident_date__lte=date_to)

        # --- FILTERS ---
        # 1. Total Incidents
        total_incidents = incidents.count()
        context["total_incidents"] = total_incidents

        # --- A. CARGA DE TRABAJO ---
        
        # 2. Incidentes por Visita
        # We need the count of visits that match the filters
        from audits.models import AuditVisit
        visits = AuditVisit.objects.all()
        if not self.request.user.is_staff:
            visits = visits.filter(inspector=self.request.user)
        
        if company:
            visits = visits.filter(company__name__icontains=company)
        if site:
            visits = visits.filter(site__name__icontains=site)
        if date_from:
            visits = visits.filter(visit_date__gte=date_from)
        if date_to:
            visits = visits.filter(visit_date__lte=date_to)
            
        total_visits = visits.count()
        if total_visits > 0:
            context["incidents_per_visit"] = round(total_incidents / total_visits, 1)
        else:
            context["incidents_per_visit"] = 0
            
        # 3. % Incidentes con análisis completo (Why 1, 2, 3 present)
        # We assume "complete" means at least 3 whys are filled
        full_analysis_count = incidents.exclude(why_1="").exclude(why_2="").exclude(why_3="").count()
        if total_incidents > 0:
             context["pct_full_analysis"] = round((full_analysis_count / total_incidents) * 100, 1)
        else:
             context["pct_full_analysis"] = 0

        # 4. % Incidentes con evidencia (at least one attachment)
        # Distinct because one incident can have multiple attachments
        incidents_with_evidence = incidents.filter(attachments__isnull=False).distinct().count()
        if total_incidents > 0:
            context["pct_evidence"] = round((incidents_with_evidence / total_incidents) * 100, 1)
        else:
            context["pct_evidence"] = 0

        # 5. Acciones por incidente
        if total_incidents > 0:
            context["actions_per_incident"] = round(actions.count() / total_incidents, 1)
        else:
            context["actions_per_incident"] = 0


        # --- B. RIESGO Y PREVENCION ---

        # 6. Incidentes por Nivel de Riesgo
        context["incidents_by_risk"] = (
            incidents.values("risk_level")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        context["risk_labels"] = json.dumps([x["risk_level"] for x in context["incidents_by_risk"]])
        context["risk_data"] = json.dumps([x["count"] for x in context["incidents_by_risk"]])

        # 7. % Incidentes Alto + Crítico
        high_critical_count = incidents.filter(risk_level__in=[Incident.RiskLevel.HIGH, Incident.RiskLevel.CRITICAL]).count()
        if total_incidents > 0:
            context["pct_high_critical"] = round((high_critical_count / total_incidents) * 100, 1)
        else:
            context["pct_high_critical"] = 0

        # 8. Top 5 Sectors
        # Group by 'sector__name' or 'sector_text' if FK is null is tricky in pure SQL group by simple annotated queryset
        # simpler approach: use sector__name and ignore text for top metrics or coalesce
        context["top_sectors"] = (
            incidents.values(name=Coalesce("sector__name", "sector_text"))
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        # 9. Relación Dominio vs Riesgo
        # Example: % of High/Critical risks where Task Mastery is Low/Unknown
        high_risk_incidents = incidents.filter(risk_level__in=[Incident.RiskLevel.HIGH, Incident.RiskLevel.CRITICAL])
        hr_total = high_risk_incidents.count()
        if hr_total > 0:
            low_mastery_hr = high_risk_incidents.filter(task_mastery__in=[Incident.TaskMastery.LOW, Incident.TaskMastery.UNKNOWN]).count()
            context["pct_high_risk_low_mastery"] = round((low_mastery_hr / hr_total) * 100, 1)
        else:
            context["pct_high_risk_low_mastery"] = 0


        # --- C. GESTION DE ACCIONES ---

        # 10. % Acciones cerradas
        total_actions = actions.count()
        closed_actions = actions.filter(status=Action.Status.DONE).count()
        open_actions = total_actions - closed_actions
        
        context["total_actions"] = total_actions
        context["open_actions"] = open_actions
        
        if total_actions > 0:
            context["closure_rate"] = round((closed_actions / total_actions) * 100, 1)
        else:
            context["closure_rate"] = 0

        # 11. Acciones abiertas por responsable (Top 5)
        context["open_actions_by_owner"] = (
            actions.filter(status__in=[Action.Status.PENDING, Action.Status.IN_PROGRESS])
            .exclude(owner_name="")
            .values("owner_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        # 16. Actions by Status (For Chart) - JSON
        status_qs = (
            actions.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        s_labels = []
        s_data = []
        for x in status_qs:
            label = Action.Status(x["status"]).label
            s_labels.append(str(label))
            s_data.append(x["count"])
        context["status_labels"] = json.dumps(s_labels)
        context["status_data"] = json.dumps(s_data)

        # 12. Tiempo promedio de cierre (días)
        # Using python calc for simplicity + timezone awareness safety (sqlite)
        closed_qs = actions.filter(status=Action.Status.DONE, closure_date__isnull=False)
        durations = []
        for a in closed_qs:
            end = a.closure_date
            start = a.execution_date if a.execution_date else a.created_at.date()
            if end and start and end >= start:
                durations.append((end - start).days)
        
        if durations:
            context["avg_closure_time"] = round(sum(durations) / len(durations), 1)
        else:
            context["avg_closure_time"] = 0

        # 13. % Acciones vencidas (Pendientes > 14 días)
        # Import timezone for reliable date math
        from django.utils import timezone
        import datetime
        limit_date = timezone.now().date() - datetime.timedelta(days=14)
        
        overdue_count = actions.filter(
            status__in=[Action.Status.PENDING, Action.Status.IN_PROGRESS],
            created_at__date__lt=limit_date
        ).count()
        
        # Denominator: Open actions or Total? Usually % of Open Actions that are overdue, or % of Total pending. 
        # User said "% Acciones vencidas". Let's use % of Total Open Actions to show health of backlog.
        if open_actions > 0:
            context["pct_overdue"] = round((overdue_count / open_actions) * 100, 1)
        else:
            context["pct_overdue"] = 0


        # --- D. EFICACIA Y MEJORA ---

        # 14. Eficacia Teórica vs Práctica
        # Count where both stats are recorded and are different?
        # Or just show distribution?
        # User said "Difference between theoretical vs practical".
        # Let's count how many had High Theoretical but Low/Med Practical.
        # This is "Efficacy Drop".
        efficacy_drop_count = actions.filter(
            effectiveness_theoretical=Action.Effectiveness.HIGH,
            effectiveness_practical__in=[Action.Effectiveness.MEDIUM, Action.Effectiveness.LOW]
        ).count()
        context["efficacy_drop_count"] = efficacy_drop_count

        # 15. % Incidentes con observación de mejora
        improvement_count = incidents.exclude(improvement_observation="").count()
        if total_incidents > 0:
            context["pct_improvement"] = round((improvement_count / total_incidents) * 100, 1)
        else:
            context["pct_improvement"] = 0


        # --- CHARTS DATA RETAINED ---
        # A) Incidents by Type
        type_qs = (
            incidents.values("incident_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        context["type_labels"] = json.dumps([
            str(Incident.IncidentType(x["incident_type"]).label) for x in type_qs
        ])
        context["type_data"] = json.dumps([x["count"] for x in type_qs])

        # B) Incidentes Over Time
        time_qs = (
            incidents.annotate(month=TruncMonth("incident_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        context["time_labels"] = json.dumps([x["month"].strftime("%Y-%m") if x["month"] else "N/A" for x in time_qs])
        context["time_data"] = json.dumps([x["count"] for x in time_qs])
        
        # C) Top Sites (Already calculated generally, but for chart specifically if needed)
        context["top_sites"] = (
            incidents.values("visit__site__name")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        return context

from .utils import render_to_pdf
from django.views import View
from django.http import HttpResponse

class DashboardPDFView(DashboardView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context['request'] = request
        pdf = render_to_pdf('pdf/dashboard_pdf.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Tablero_%s.pdf" % (request.user.username)
            content = "inline; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")


# --- Quick Add Views ---
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Company, Site, Sector

class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    fields = ["name", "tax_id", "notes"]
    template_name = "core/quick_add_form.html"
    
    def get_success_url(self):
        # Return to the previous page (audit form) if possible, or dashboard
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nueva Empresa"
        return ctx


class SiteCreateView(LoginRequiredMixin, CreateView):
    model = Site
    fields = ["company", "name", "address", "city"]
    template_name = "core/quick_add_form.html"

    def get_initial(self):
        initial = super().get_initial()
        # Pre-select company if passed in GET
        company_id = self.request.GET.get("company")
        if company_id:
            initial["company"] = company_id
        return initial

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("dashboard")
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nueva Obra / Sitio"
        return ctx


class SectorCreateView(LoginRequiredMixin, CreateView):
    model = Sector
    fields = ["company", "name"]
    template_name = "core/quick_add_form.html"

    def get_initial(self):
        initial = super().get_initial()
        company_id = self.request.GET.get("company")
        if company_id:
            initial["company"] = company_id
        return initial

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        if next_url:
            return next_url
        return reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Nuevo Sector"
        return ctx
