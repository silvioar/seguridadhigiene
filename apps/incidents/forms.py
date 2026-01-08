# apps/incidents/forms.py
from django import forms
from django.forms import inlineformset_factory

from .models import Incident, Action, IncidentAttachment


class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            "visit",
            "investigation_date",
            "incident_number",
            "incident_date",
            "incident_time",
            "incident_type",
            "sector",
            "sector_text",
            "task_performed",
            "task_mastery",
            "description",
            "operator_name",
            "operator_sector",
            "operator_position",
            "operator_seniority",
            "responsible_name",
            "responsible_role",
            "risk_level",
            "cause_number",
            "why_1",
            "why_2",
            "why_3",
            "why_4",
            "why_5",
            "legal_framework_internal",
            "improvement_observation",
        ]
        widgets = {
            "investigation_date": forms.DateInput(attrs={"type": "date"}),
            "incident_date": forms.DateInput(attrs={"type": "date"}),
            "incident_time": forms.TimeInput(attrs={"type": "time"}),
            "description": forms.Textarea(attrs={"rows": 4}),
            "why_1": forms.Textarea(attrs={"rows": 2}),
            "why_2": forms.Textarea(attrs={"rows": 2}),
            "why_3": forms.Textarea(attrs={"rows": 2}),
            "why_4": forms.Textarea(attrs={"rows": 2}),
            "why_5": forms.Textarea(attrs={"rows": 2}),
            "improvement_observation": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        cleaned = super().clean()

        # Si no eligieron sector del catálogo, exigir sector_text (mínimo de data quality)
        sector = cleaned.get("sector")
        sector_text = (cleaned.get("sector_text") or "").strip()
        if not sector and not sector_text:
            self.add_error("sector_text", "Ingresá un sector (texto) o seleccioná uno del catálogo.")

        return cleaned


class ActionForm(forms.ModelForm):
    class Meta:
        model = Action
        fields = [
            "action_type",
            "description",
            "owner_name",
            "status",
            "execution_date",
            "closure_date",
            "effectiveness_theoretical",
            "effectiveness_practical",
        ]
        widgets = {
            "execution_date": forms.DateInput(attrs={"type": "date"}),
            "closure_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
        }

    def clean(self):
        cleaned = super().clean()
        execution = cleaned.get("execution_date")
        closure = cleaned.get("closure_date")
        if execution and closure and closure < execution:
            self.add_error("closure_date", "La fecha de cierre no puede ser anterior a la ejecución.")
        return cleaned


class IncidentAttachmentForm(forms.ModelForm):
    class Meta:
        model = IncidentAttachment
        fields = ["file", "caption"]


# Inline formsets
ImmediateActionFormSet = inlineformset_factory(
    parent_model=Incident,
    model=Action,
    form=ActionForm,
    fields=ActionForm.Meta.fields,
    extra=1,
    can_delete=True,
)

CorrectiveActionFormSet = inlineformset_factory(
    parent_model=Incident,
    model=Action,
    form=ActionForm,
    fields=ActionForm.Meta.fields,
    extra=1,
    can_delete=True,
)

AttachmentFormSet = inlineformset_factory(
    parent_model=Incident,
    model=IncidentAttachment,
    form=IncidentAttachmentForm,
    fields=["file", "caption"],
    extra=1,
    can_delete=True,
)
