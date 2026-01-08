# apps/audits/forms.py
from django import forms
from .models import AuditVisit


class AuditVisitForm(forms.ModelForm):
    class Meta:
        model = AuditVisit
        fields = ["company", "site", "sector", "visit_date", "notes"]
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
