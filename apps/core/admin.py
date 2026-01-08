# apps/core/admin.py
from django.contrib import admin
from .models import Company, Site, Sector


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "tax_id", "created_at")
    search_fields = ("name", "tax_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "city", "province", "active", "created_at")
    list_filter = ("company", "active", "province")
    search_fields = ("name", "company__name", "address", "city", "province")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "company", "created_at")
    list_filter = ("company",)
    search_fields = ("name", "company__name")
    readonly_fields = ("created_at", "updated_at")
