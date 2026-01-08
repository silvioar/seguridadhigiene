# apps/audits/admin.py
from django.contrib import admin
from .models import AuditVisit


@admin.register(AuditVisit)
class AuditVisitAdmin(admin.ModelAdmin):
    list_display = ("id", "visit_date", "company", "site", "sector", "inspector", "created_at")
    list_filter = ("visit_date", "company", "site", "inspector")
    search_fields = ("company__name", "site__name", "notes", "inspector__username", "inspector__email")
    date_hierarchy = "visit_date"
    readonly_fields = ("created_at", "updated_at")
