# apps/audits/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Company, Site, Sector, TimeStampedModel


class AuditVisit(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="visits")
    site = models.ForeignKey(Site, on_delete=models.PROTECT, related_name="visits")
    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name="visits"
    )

    visit_date = models.DateField(default=timezone.localdate, db_index=True)
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="audit_visits"
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-visit_date", "-created_at"]
        indexes = [
            models.Index(fields=["company", "visit_date"]),
            models.Index(fields=["site", "visit_date"]),
        ]

    def __str__(self):
        return f"Visita {self.visit_date} - {self.site}"
