# apps/audits/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, DetailView, ListView

from .models import AuditVisit
from .forms import AuditVisitForm
from incidents.models import Incident


class VisitListView(LoginRequiredMixin, ListView):
    model = AuditVisit
    template_name = "audits/visit_list.html"
    paginate_by = 25

    def get_queryset(self):
        qs = AuditVisit.objects.select_related("company", "site", "sector", "inspector").order_by("-visit_date", "-created_at")
        if not self.request.user.is_staff:
            qs = qs.filter(inspector=self.request.user)
        
        # Filtros
        company = self.request.GET.get("company")
        site = self.request.GET.get("site")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if company:
            qs = qs.filter(company__name__icontains=company)
        if site:
            qs = qs.filter(site__name__icontains=site)
        if date_from:
            qs = qs.filter(visit_date__gte=date_from)
        if date_to:
            qs = qs.filter(visit_date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Company, Site
        context["companies"] = Company.objects.all().order_by("name")
        context["sites"] = Site.objects.select_related("company").order_by("company__name", "name")
        return context


class VisitCreateView(LoginRequiredMixin, CreateView):
    model = AuditVisit
    form_class = AuditVisitForm
    template_name = "audits/visit_form.html"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.inspector = self.request.user
        obj.save()
        self.object = obj
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("audits:detail", kwargs={"pk": self.object.pk})


class VisitDetailView(LoginRequiredMixin, DetailView):
    model = AuditVisit
    template_name = "audits/visit_detail.html"

    def get_queryset(self):
        qs = AuditVisit.objects.select_related("company", "site", "sector", "inspector")
        if not self.request.user.is_staff:
            qs = qs.filter(inspector=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["incidents"] = (
            Incident.objects.filter(visit=self.object)
            .order_by("-incident_date", "-created_at")
        )
        return ctx
