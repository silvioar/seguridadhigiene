import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Company, Site, Sector
from audits.models import AuditVisit
from incidents.models import Incident, Action, IncidentAttachment

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds the database with 10 demo incidents regarding Safety & Hygiene"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Starting demo data seeding..."))
        
        # 1. Company
        company, _ = Company.objects.get_or_create(
            name="ACME Construcciones S.A.",
            defaults={"tax_id": "30-12345678-9"}
        )
        
        # 2. Sites (Obras/Plantas)
        sites_data = [
            "Obra Torre Centro – Etapa 2",
            "Planta Industrial Sur",
            "Edificio Oficinas Norte",
        ]
        sites = {}
        for s_name in sites_data:
            site, _ = Site.objects.get_or_create(company=company, name=s_name)
            sites[s_name] = site

        # 3. User (Inspector)
        inspector_username = "laura.martinez"
        inspector, created = User.objects.get_or_create(
            username=inspector_username,
            defaults={
                "email": "laura.martinez@acme.com",
                "first_name": "Laura",
                "last_name": "Martínez",
                "is_staff": True
            }
        )
        if created:
            inspector.set_password("securepassword123")
            inspector.save()
            self.stdout.write(f"User {inspector_username} created.")

        # 4. Sectors (Catalog)
        sectors_to_create = [
            "Losa nivel 6 – Estructura",
            "Estructura",
            "Circulaciones",
            "Depósito",
            "Taller",
            "Escaleras",
            "Oficinas",
        ]
        sectors_map = {}
        for sec_name in sectors_to_create:
            sec_obj, _ = Sector.objects.get_or_create(company=company, name=sec_name)
            sectors_map[sec_name] = sec_obj

        # 5. Incidents Data
        # Base date for reference: 2026-01-08 to 2026-01-13
        # We'll use the exact data provided.

        incidents_data = [
            {
                "site": "Obra Torre Centro – Etapa 2",
                "date": "2026-01-08",
                "time": "09:35",
                "type": Incident.IncidentType.UNSAFE_CONDITION,
                "sector": "Losa nivel 6 – Estructura",
                "task": "Encofrado",
                "risk": Incident.RiskLevel.HIGH,
                "desc": "Borde de losa sin baranda ni red de protección.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Se instaló baranda provisoria."},
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.IN_PROGRESS, "desc": "Revisar resto del perímetro."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.DONE, "desc": "Capacitación en altura (charla 5 min)."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.IN_PROGRESS, "desc": "Compra de redes faltantes."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.IN_PROGRESS, "desc": "Sanción al capataz."},
                ]
            },
            {
                "site": "Obra Torre Centro – Etapa 2",
                "date": "2026-01-08",
                "time": "11:10",
                "type": Incident.IncidentType.UNSAFE_ACT,
                "sector": "Estructura",
                "task": "Movimiento manual de cargas",
                "risk": Incident.RiskLevel.MEDIUM,
                "desc": "Operario levantando cargas >25kg sin ayuda mecánica.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Detenciòn de tarea y corrección postural."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Solicitar zorra hidráulica para el sector."},
                ]
            },
            {
                "site": "Obra Torre Centro – Etapa 2",
                "date": "2026-01-08",
                "time": "14:20",
                "type": Incident.IncidentType.NEAR_MISS,
                "sector": "Circulaciones",
                "task": "Traslado peatonal",
                "risk": Incident.RiskLevel.MEDIUM,
                "desc": "Peatón casi impactado por autoelevador sin alarma sonora.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Reparación provisoria de alarma."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.DONE, "desc": "Plan de mantenimiento preventivo autoelevadores."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.IN_PROGRESS, "desc": "Demarcación de sendas peatonales."},
                ]
            },
            {
                "site": "Planta Industrial Sur",
                "date": "2026-01-09",
                "time": "08:50",
                "type": Incident.IncidentType.UNSAFE_CONDITION,
                "sector": "Depósito",
                "task": "Almacenamiento",
                "risk": Incident.RiskLevel.HIGH,
                "desc": "Estanterías sobrecargadas sin señalización de carga máxima.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Aliviar carga excedente."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Cálculo estructural de estanterías."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Cartelería de Carga Máxima Admisible."},
                ]
            },
            {
                "site": "Planta Industrial Sur",
                "date": "2026-01-09",
                "time": "10:40",
                "type": Incident.IncidentType.INCIDENT,
                "sector": "Taller",
                "task": "Uso de amoladora",
                "risk": Incident.RiskLevel.CRITICAL,
                "desc": "Corte leve en mano por uso de herramienta sin guarda instalada.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Primeros auxilios en enfermería."},
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Retiro de herramienta defectuosa."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.DONE, "desc": "Re-inducción uso de herramientas de poder."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.IN_PROGRESS, "desc": "Auditoría de todas las amoladoras."},
                ]
            },
            {
                "site": "Planta Industrial Sur",
                "date": "2026-01-10",
                "time": "15:15",
                "type": Incident.IncidentType.UNSAFE_ACT,
                "sector": "Taller",
                "task": "Soldadura",
                "risk": Incident.RiskLevel.MEDIUM,
                "desc": "Operario soldando sin protección ocular adecuada.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Provisión de máscara fotosensible."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Checklist de EPP antes de inicio de turno."},
                ]
            },
            {
                "site": "Edificio Oficinas Norte",
                "date": "2026-01-11",
                "time": "09:05",
                "type": Incident.IncidentType.UNSAFE_CONDITION,
                "sector": "Escaleras",
                "task": "Circulación",
                "risk": Incident.RiskLevel.LOW,
                "desc": "Escalón con superficie resbaladiza por limpieza reciente sin señalización.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Colocación de cartel Piso Mojado."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.DONE, "desc": "Instrucción a personal de limpieza."},
                ]
            },
            {
                "site": "Edificio Oficinas Norte",
                "date": "2026-01-11",
                "time": "13:30",
                "type": Incident.IncidentType.NEAR_MISS,
                "sector": "Oficinas",
                "task": "Uso de escalera portátil",
                "risk": Incident.RiskLevel.MEDIUM,
                "desc": "Escalera mal apoyada, casi provoca caída al subir.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Sujeción correcta de escalera."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Compra de escaleras con base antideslizante."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Procedimiento de trabajo seguro en altura baja."},
                ]
            },
            {
                "site": "Obra Torre Centro – Etapa 2",
                "date": "2026-01-12",
                "time": "16:00",
                "type": Incident.IncidentType.UNSAFE_ACT,
                "sector": "Estructura",
                "task": "Trabajo en altura",
                "risk": Incident.RiskLevel.HIGH,
                "desc": "Uso incorrecto de arnés sin línea de vida conectada.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Anclaje inmediato a línea de vida."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.IN_PROGRESS, "desc": "Curso de trabajos en altura obligatorio."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.PENDING, "desc": "Instalación de líneas de vida definitivas en sector."},
                ]
            },
            {
                "site": "Obra Torre Centro – Etapa 2",
                "date": "2026-01-13",
                "time": "08:15",
                "type": Incident.IncidentType.UNSAFE_CONDITION,
                "sector": "Depósito",
                "task": "Orden y limpieza",
                "risk": Incident.RiskLevel.MEDIUM,
                "desc": "Materiales obstruyendo vías de evacuación.",
                "actions": [
                    {"type": Action.ActionType.IMMEDIATE, "status": Action.Status.DONE, "desc": "Despeje de pasillo."},
                    {"type": Action.ActionType.CORRECTIVE, "status": Action.Status.DONE, "desc": "Delimitación de áreas de acopio."},
                ]
            },
        ]

        # 6. Create Loop
        for i, item in enumerate(incidents_data, start=1):
            s_obj = sites[item["site"]]
            sec_obj = sectors_map.get(item["sector"])
            
            # Create/Get Visit for that day/site
            visit, _ = AuditVisit.objects.get_or_create(
                company=company,
                site=s_obj,
                visit_date=item["date"],
                inspector=inspector,
                defaults={"notes": "Visita automática demo."}
            )

            # Check if incident exists (to avoid duplication if run multiple times)
            # Strategy: look for same description on same visit
            incident, created_inc = Incident.objects.get_or_create(
                visit=visit,
                description=item["desc"],
                defaults={
                    "incident_number": i,
                    "incident_date": item["date"],
                    "incident_time": item["time"],
                    "incident_type": item["type"],
                    "sector": sec_obj,
                    "sector_text": item["sector"],
                    "task_performed": item["task"],
                    "risk_level": item["risk"],
                    "operator_name": "Juan Perez (Demo)",  # Dummy
                    "responsible_name": "Carlos Gomez (Capataz Demo)", # Dummy
                }
            )

            if created_inc:
                self.stdout.write(f"Incidente {i} creado: {item['desc'][:30]}...")
            else:
                self.stdout.write(f"Incidente {i} ya existe.")
                # If exists, we skip creating actions to avoid finding them again and again or duplicating?
                # For safety, let's skip actions if incident wasn't created.
                continue

            # Create Actions
            for act_data in item["actions"]:
                Action.objects.create(
                    incident=incident,
                    action_type=act_data["type"],
                    status=act_data["status"],
                    description=act_data["desc"],
                    owner_name="Responsable Demo",
                    closure_date=visit.visit_date if act_data["status"] == Action.Status.DONE else None
                )

        self.stdout.write(self.style.SUCCESS("All demo data seeded successfully!"))
