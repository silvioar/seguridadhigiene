# apps/incidents/admin.py
from django.contrib import admin
from django.utils.html import format_html

from .models import Incident, Action, IncidentAttachment


class ActionInline(admin.TabularInline):
    model = Action
    extra = 0
    fields = (
        "action_type",
        "description",
        "owner_name",
        "status",
        "execution_date",
        "closure_date",
        "effectiveness_theoretical",
        "effectiveness_practical",
    )
    autocomplete_fields = []


class IncidentAttachmentInline(admin.TabularInline):
    model = IncidentAttachment
    extra = 0
    fields = ("file", "caption", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "incident_date",
        "incident_time",
        "incident_type",
        "risk_level",
        "site_name",
        "sector_display",
        "responsible_name",
        "actions_open_count",
        "created_at",
    )
    list_filter = (
        "incident_type",
        "risk_level",
        "task_mastery",
        "visit__company",
        "visit__site",
        "created_at",
    )
    search_fields = (
        "description",
        "task_performed",
        "operator_name",
        "responsible_name",
        "visit__site__name",
        "visit__company__name",
        "sector_text",
        "legal_framework_internal",
    )
    date_hierarchy = "incident_date"
    readonly_fields = ("created_at", "updated_at")
    inlines = [ActionInline, IncidentAttachmentInline]

    fieldsets = (
        ("Visita / Identificación", {"fields": ("visit", "investigation_date", "incident_number")}),
        ("Suceso", {"fields": ("incident_date", "incident_time", "incident_type")}),
        ("Ubicación / Tarea", {"fields": ("sector", "sector_text", "task_performed", "task_mastery")}),
        ("Descripción", {"fields": ("description",)}),
        ("Operario", {"fields": ("operator_name", "operator_sector", "operator_position", "operator_seniority")}),
        ("Responsable", {"fields": ("responsible_name", "responsible_role")}),
        ("Causa / 5 Porqués", {"fields": ("risk_level", "cause_number", "why_1", "why_2", "why_3", "why_4", "why_5")}),
        ("Cumplimiento / Mejora", {"fields": ("legal_framework_internal", "improvement_observation")}),
        ("Sistema", {"fields": ("created_at", "updated_at")}),
    )

    def site_name(self, obj):
        return obj.visit.site.name
    site_name.short_description = "Obra"

    def sector_display(self, obj):
        return obj.sector.name if obj.sector else obj.sector_text
    sector_display.short_description = "Sector"

    def actions_open_count(self, obj):
        from .models import Action
        return obj.actions.exclude(status=Action.Status.DONE).count()
    actions_open_count.short_description = "Acciones abiertas"


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ("id", "action_type", "status", "owner_name", "incident", "execution_date", "closure_date", "created_at")
    list_filter = ("action_type", "status", "created_at")
    search_fields = ("description", "owner_name", "incident__description")
    date_hierarchy = "created_at"


@admin.register(IncidentAttachment)
class IncidentAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "incident", "caption", "uploaded_by", "created_at")
    list_filter = ("created_at",)
    search_fields = ("caption", "incident__description")
