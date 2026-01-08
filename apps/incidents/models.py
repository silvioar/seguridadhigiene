# apps/incidents/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone

from audits.models import AuditVisit
from core.models import Sector, TimeStampedModel


class Incident(TimeStampedModel):
    # --- Choices (ajustá a tu vocabulario real) ---
    class TaskMastery(models.TextChoices):
        HIGH = "HIGH", "Alto"
        MEDIUM = "MEDIUM", "Medio"
        LOW = "LOW", "Bajo"
        UNKNOWN = "UNKNOWN", "No informado"

    class RiskLevel(models.TextChoices):
        LOW = "LOW", "Bajo"
        MEDIUM = "MEDIUM", "Medio"
        HIGH = "HIGH", "Alto"
        CRITICAL = "CRITICAL", "Crítico"

    class IncidentType(models.TextChoices):
        INCIDENT = "INCIDENT", "Incidente"
        NEAR_MISS = "NEAR_MISS", "Casi incidente"
        UNSAFE_ACT = "UNSAFE_ACT", "Acto inseguro"
        UNSAFE_CONDITION = "UNSAFE_CONDITION", "Condición insegura"
        OTHER = "OTHER", "Otro"

    visit = models.ForeignKey(AuditVisit, on_delete=models.CASCADE, related_name="incidents")

    # En el Excel aparecen campos tipo: FECHA INVEST, N°, FECHA SUCESO, HS OCURRENCIA, TIPO SUCESO...
    investigation_date = models.DateField(null=True, blank=True, db_index=True)
    incident_number = models.PositiveIntegerField(null=True, blank=True)
    incident_date = models.DateField(default=timezone.localdate, db_index=True)
    incident_time = models.TimeField(null=True, blank=True)

    incident_type = models.CharField(
        max_length=40, choices=IncidentType.choices, default=IncidentType.INCIDENT
    )

    # Sector puede venir del catálogo o texto libre
    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents"
    )
    sector_text = models.CharField(max_length=120, blank=True, default="")

    task_performed = models.CharField(max_length=255, blank=True, default="")
    task_mastery = models.CharField(
        max_length=20, choices=TaskMastery.choices, default=TaskMastery.UNKNOWN
    )

    description = models.TextField()

    # Operario (snapshot)
    operator_name = models.CharField(max_length=180, blank=True, default="")
    operator_sector = models.CharField(max_length=120, blank=True, default="")
    operator_position = models.CharField(max_length=120, blank=True, default="")
    operator_seniority = models.CharField(max_length=60, blank=True, default="")  # texto libre (años/meses)

    # Responsable (snapshot)
    responsible_name = models.CharField(max_length=180, blank=True, default="")
    responsible_role = models.CharField(max_length=120, blank=True, default="")

    # Análisis causal / 5 porqués
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)
    cause_number = models.CharField(max_length=40, blank=True, default="")
    why_1 = models.TextField(blank=True, default="")
    why_2 = models.TextField(blank=True, default="")
    why_3 = models.TextField(blank=True, default="")
    why_4 = models.TextField(blank=True, default="")
    why_5 = models.TextField(blank=True, default="")

    # Cumplimiento / mejora (Excel: MARCO LEGAL INTERNO + OBSERVACION MEJORA)
    legal_framework_internal = models.CharField(max_length=255, blank=True, default="")
    improvement_observation = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-incident_date", "-created_at"]
        indexes = [
            models.Index(fields=["visit", "incident_date"]),
            models.Index(fields=["incident_type", "incident_date"]),
            models.Index(fields=["risk_level", "incident_date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["visit", "incident_number"],
                name="uq_incident_visit_number",
                condition=models.Q(incident_number__isnull=False),
            )
        ]

    def __str__(self):
        num = f" #{self.incident_number}" if self.incident_number else ""
        return f"Incidente{num} - {self.incident_date} - {self.visit.site.name}"


class Action(TimeStampedModel):
    class ActionType(models.TextChoices):
        IMMEDIATE = "IMMEDIATE", "Acción inmediata"
        CORRECTIVE = "CORRECTIVE", "Acción correctiva"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pendiente"
        IN_PROGRESS = "IN_PROGRESS", "En proceso"
        DONE = "DONE", "Cerrada"

    class Effectiveness(models.TextChoices):
        HIGH = "HIGH", "Alta"
        MEDIUM = "MEDIUM", "Media"
        LOW = "LOW", "Baja"
        NA = "NA", "No aplica"

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="actions")

    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    description = models.TextField()

    owner_name = models.CharField(max_length=180, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    execution_date = models.DateField(null=True, blank=True, db_index=True)
    closure_date = models.DateField(null=True, blank=True, db_index=True)

    # Solo aplica a correctivas normalmente (pero lo dejamos libre)
    effectiveness_theoretical = models.CharField(
        max_length=10, choices=Effectiveness.choices, default=Effectiveness.NA
    )
    effectiveness_practical = models.CharField(
        max_length=10, choices=Effectiveness.choices, default=Effectiveness.NA
    )

    class Meta:
        ordering = ["action_type", "status", "-created_at"]
        indexes = [
            models.Index(fields=["action_type", "status"]),
            models.Index(fields=["status", "closure_date"]),
        ]

    def __str__(self):
        return f"{self.get_action_type_display()} - {self.get_status_display()}"


class IncidentAttachment(TimeStampedModel):
    """
    Evidencia: fotos / PDFs.
    Para MVP: asociamos al incidente (no a la acción). Si querés, luego agregás FK opcional a Action.
    """
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="incidents/%Y/%m/%d/")
    caption = models.CharField(max_length=255, blank=True, default="")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incident_files"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.caption or f"Adjunto {self.id}"
