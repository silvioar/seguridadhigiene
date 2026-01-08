# apps/core/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    name = models.CharField(max_length=180, unique=True)
    tax_id = models.CharField("CUIT/CUIL", max_length=20, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Site(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sites")
    name = models.CharField(max_length=180)
    address = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=120, blank=True, default="")
    province = models.CharField(max_length=120, blank=True, default="")
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["company__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="uq_site_company_name")
        ]

    def __str__(self):
        return f"{self.company.name} - {self.name}"


class Sector(TimeStampedModel):
    """
    Catálogo simple (opcional). Si preferís texto libre, podés no usarlo en formularios.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="sectors")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["company__name", "name"]
        constraints = [
            models.UniqueConstraint(fields=["company", "name"], name="uq_sector_company_name")
        ]

    def __str__(self):
        return f"{self.company.name} - {self.name}"
