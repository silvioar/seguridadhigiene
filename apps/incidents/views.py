# apps/incidents/views.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import CreateView, UpdateView, DetailView, ListView

from audits.models import AuditVisit
from .models import Incident, Action
from .forms import (
    IncidentForm,
    ImmediateActionFormSet,
    CorrectiveActionFormSet,
    AttachmentFormSet,
)


class IncidentListView(LoginRequiredMixin, ListView):
    model = Incident
    template_name = "incidents/incident_list.html"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Incident.objects.select_related("visit", "visit__company", "visit__site")
            .order_by("-incident_date", "-created_at")
        )

        # Inspector ve solo lo suyo (admin/staff ve todo)
        if not self.request.user.is_staff:
            qs = qs.filter(visit__inspector=self.request.user)

        # filtros simples por GET
        company = self.request.GET.get("company")
        site = self.request.GET.get("site")
        risk = self.request.GET.get("risk_level")
        i_type = self.request.GET.get("incident_type")
        date_from = self.request.GET.get("date_from")
        date_to = self.request.GET.get("date_to")

        if company:
            # Try to filter by name, if numeric assume ID
            if company.isdigit():
                qs = qs.filter(visit__company_id=company)
            else:
                qs = qs.filter(visit__company__name__icontains=company)
        
        if site:
            # Same strategy for site
            if site.isdigit():
                qs = qs.filter(visit__site_id=site)
            else:
                qs = qs.filter(visit__site__name__icontains=site)

        if risk:
            qs = qs.filter(risk_level=risk)
        
        if i_type:
            qs = qs.filter(incident_type=i_type)

        if date_from:
            qs = qs.filter(incident_date__gte=date_from)
        
        if date_to:
            qs = qs.filter(incident_date__lte=date_to)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.models import Company, Site
        context["companies"] = Company.objects.all().order_by("name")
        context["sites"] = Site.objects.select_related("company").order_by("company__name", "name")
        return context


class IncidentDetailView(LoginRequiredMixin, DetailView):
    model = Incident
    template_name = "incidents/incident_detail.html"

    def get_queryset(self):
        qs = Incident.objects.select_related("visit", "visit__company", "visit__site").prefetch_related("actions", "attachments")
        if not self.request.user.is_staff:
            qs = qs.filter(visit__inspector=self.request.user)
        return qs


class IncidentCreateView(LoginRequiredMixin, CreateView):
    model = Incident
    form_class = IncidentForm
    template_name = "incidents/incident_form.html"

    def get_initial(self):
        initial = super().get_initial()
        visit_id = self.request.GET.get("visit")
        if visit_id:
            initial["visit"] = visit_id
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx["immediate_formset"] = ImmediateActionFormSet(self.request.POST, prefix="imm")
            ctx["corrective_formset"] = CorrectiveActionFormSet(self.request.POST, prefix="cor")
            ctx["attachment_formset"] = AttachmentFormSet(self.request.POST, self.request.FILES, prefix="att")
        else:
            ctx["immediate_formset"] = ImmediateActionFormSet(prefix="imm")
            ctx["corrective_formset"] = CorrectiveActionFormSet(prefix="cor")
            ctx["attachment_formset"] = AttachmentFormSet(prefix="att")
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        imm_fs = context["immediate_formset"]
        cor_fs = context["corrective_formset"]
        att_fs = context["attachment_formset"]

        # Si no es staff, forzamos que la visita sea del inspector
        visit = form.cleaned_data["visit"]
        if not self.request.user.is_staff and visit.inspector_id != self.request.user.id:
            form.add_error("visit", "No podés cargar incidentes en visitas de otro inspector.")
            return self.form_invalid(form)

        if not (imm_fs.is_valid() and cor_fs.is_valid() and att_fs.is_valid()):
            return self.form_invalid(form)

        self.object = form.save()

        # Guardar acciones: filtramos por tipo
        imm_instances = imm_fs.save(commit=False)
        for inst in imm_instances:
            inst.incident = self.object
            inst.action_type = Action.ActionType.IMMEDIATE
            inst.save()
        for obj in imm_fs.deleted_objects:
            obj.delete()

        cor_instances = cor_fs.save(commit=False)
        for inst in cor_instances:
            inst.incident = self.object
            inst.action_type = Action.ActionType.CORRECTIVE
            inst.save()
        for obj in cor_fs.deleted_objects:
            obj.delete()

        # Adjuntos
        att_instances = att_fs.save(commit=False)
        for inst in att_instances:
            inst.incident = self.object
            inst.uploaded_by = self.request.user
            inst.save()
        for obj in att_fs.deleted_objects:
            obj.delete()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("incidents:detail", kwargs={"pk": self.object.pk})


class IncidentUpdateView(LoginRequiredMixin, UpdateView):
    model = Incident
    form_class = IncidentForm
    template_name = "incidents/incident_form.html"

    def get_queryset(self):
        qs = Incident.objects.select_related("visit")
        if not self.request.user.is_staff:
            qs = qs.filter(visit__inspector=self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        qs_imm = self.object.actions.filter(action_type=Action.ActionType.IMMEDIATE)
        qs_cor = self.object.actions.filter(action_type=Action.ActionType.CORRECTIVE)

        if self.request.POST:
            ctx["immediate_formset"] = ImmediateActionFormSet(self.request.POST, instance=self.object, queryset=qs_imm, prefix="imm")
            ctx["corrective_formset"] = CorrectiveActionFormSet(self.request.POST, instance=self.object, queryset=qs_cor, prefix="cor")
            ctx["attachment_formset"] = AttachmentFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix="att")
        else:
            ctx["immediate_formset"] = ImmediateActionFormSet(instance=self.object, queryset=qs_imm, prefix="imm")
            ctx["corrective_formset"] = CorrectiveActionFormSet(instance=self.object, queryset=qs_cor, prefix="cor")
            ctx["attachment_formset"] = AttachmentFormSet(instance=self.object, prefix="att")
        return ctx

    @transaction.atomic
    def form_valid(self, form):
        context = self.get_context_data()
        imm_fs = context["immediate_formset"]
        cor_fs = context["corrective_formset"]
        att_fs = context["attachment_formset"]

        if not (imm_fs.is_valid() and cor_fs.is_valid() and att_fs.is_valid()):
            return self.form_invalid(form)

        self.object = form.save()

        # Acciones inmediatas
        imm_instances = imm_fs.save(commit=False)
        for inst in imm_instances:
            inst.incident = self.object
            inst.action_type = Action.ActionType.IMMEDIATE
            inst.save()
        for obj in imm_fs.deleted_objects:
            obj.delete()

        # Acciones correctivas
        cor_instances = cor_fs.save(commit=False)
        for inst in cor_instances:
            inst.incident = self.object
            inst.action_type = Action.ActionType.CORRECTIVE
            inst.save()
        for obj in cor_fs.deleted_objects:
            obj.delete()

        # Adjuntos
        att_instances = att_fs.save(commit=False)
        for inst in att_instances:
            inst.incident = self.object
            if not inst.uploaded_by_id:
                inst.uploaded_by = self.request.user
            inst.save()
        for obj in att_fs.deleted_objects:
            obj.delete()

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("incidents:detail", kwargs={"pk": self.object.pk})

from core.utils import render_to_pdf
from django.http import HttpResponse

class IncidentDetailPDFView(IncidentDetailView):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        context['request'] = request
        pdf = render_to_pdf('pdf/incident_detail_pdf.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = "Incidente_%s_%s.pdf" % (self.object.pk, request.user.username)
            content = "inline; filename='%s'" % (filename)
            response['Content-Disposition'] = content
            return response
        return HttpResponse("Not found")
