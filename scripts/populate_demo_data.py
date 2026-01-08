
import random
from datetime import date, timedelta, time
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import Company, Site, Sector
from audits.models import AuditVisit
from incidents.models import Incident, Action

User = get_user_model()

def create_demo_data():
    print("Starting demo data generation...")

    # 1. Setup Base Data
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("No superuser found. Please create one first.")
        return

    company, _ = Company.objects.get_or_create(name="ACME Construcciones S.A.", defaults={"tax_id": "30-12345678-9"})
    site, _ = Site.objects.get_or_create(name="Obra Torre Centro – Etapa 2", company=company, defaults={"address": "Av. Corrientes 1234"})

    sectors = ["Estructura", "Excavación", "Altura", "Oficina Técnica", "Acopio", "Fachada"]
    sector_objs = []
    for s_name in sectors:
        sec, _ = Sector.objects.get_or_create(name=s_name, company=company)
        sector_objs.append(sec)

    # 2. Define Dates (Dec 2025 - Jan 2026)
    # Today is roughly 2026-01-08 according to context.
    # We want some in Dec, some in Jan.
    
    dates = [
        date(2025, 12, 5), date(2025, 12, 12), date(2025, 12, 18), date(2025, 12, 26), # Dec
        date(2026, 1, 2), date(2026, 1, 5), date(2026, 1, 7), date(2026, 1, 8), # Jan
        date(2025, 12, 10), date(2026, 1, 3) 
    ]

    incidents_created = 0

    for i, d in enumerate(dates):
        # Create or Get Visit (handle duplicates)
        visit = AuditVisit.objects.filter(site=site, visit_date=d).first()
        if not visit:
            visit = AuditVisit.objects.create(
                site=site,
                company=company,
                visit_date=d,
                inspector=admin_user,
                notes=f"Visita de rutina {d}"
            )

        # Determine Incident Attributes to ensure variety
        risk =  random.choice(Incident.RiskLevel.choices)[0]
        inc_type = random.choice(Incident.IncidentType.choices)[0]
        sector = random.choice(sector_objs)
        
        # Logic for "Task Mastery vs Risk" KPI
        # If High Risk, sometimes make Mastery Low/Unknown
        mastery = Incident.TaskMastery.HIGH
        if risk in [Incident.RiskLevel.HIGH, Incident.RiskLevel.CRITICAL] and random.random() < 0.4:
            mastery = Incident.TaskMastery.LOW
        
        # Create Incident
        inc = Incident.objects.create(
            visit=visit,
            incident_date=d,
            incident_time=time(random.randint(8, 17), random.randint(0, 59)),
            incident_type=inc_type,
            risk_level=risk,
            sector=sector,
            task_performed="Tarea de construcción general",
            task_mastery=mastery,
            description=f"Incidente de prueba #{i+1} generado para demostración de tablero.",
            why_1="Causa inmediata no detectada", 
            # Fill 3 whys randomly for KPI "% Full Analysis"
            why_2="Falta de atención" if random.random() > 0.3 else "",
            why_3="Falta de capacitación" if random.random() > 0.3 else "",
            improvement_observation="Reforzar charla de seguridad." if random.random() > 0.5 else "" # For KPI Efficacy
        )

        # Create 1-2 Actions per Incident
        for j in range(random.randint(1, 2)):
            status = Action.Status.DONE if random.random() > 0.4 else Action.Status.PENDING
            
            # Logic for Overdue KPI (Pending > 14 days)
            # If date is Dec 5 and status pending, it is likely overdue by Jan 8
            # We set created_at to incident date roughly
            # Action Model uses auto_now_add for created_at, we might need to update it manually 
            # or just rely on execution date logic if the KPI used that.
            # The KPI code used: created_at__date__lt=limit_date
            
            act = Action.objects.create(
                incident=inc,
                action_type=Action.ActionType.CORRECTIVE,
                description=f"Acción correctiva {j+1} para incidente {inc.id}",
                owner_name="Juan Perez" if random.random() > 0.5 else "Maria Gomez",
                status=status,
                execution_date=d + timedelta(days=random.randint(1, 5)), # Plan date
                
                # For Efficacy KPI
                effectiveness_theoretical=Action.Effectiveness.HIGH,
                effectiveness_practical=Action.Effectiveness.LOW if random.random() < 0.2 else Action.Effectiveness.HIGH
            )

            # Manually update created_at to simulate old actions
            # (Requires saving, then updating because auto_now_add)
            act.created_at = timezone.make_aware(timezone.datetime.combine(d, time(9, 0)))
            
            if status == Action.Status.DONE:
                act.closure_date = d + timedelta(days=random.randint(1, 10))
            
            act.save()

        incidents_created += 1

    print(f"Successfully created {incidents_created} incidents with related visits and actions.")

create_demo_data()
