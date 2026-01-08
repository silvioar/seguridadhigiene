from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone
from datetime import date, time

from core.models import Company, Site, Sector
from audits.models import AuditVisit
from incidents.models import Incident, Action, IncidentAttachment

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with demo data as requested'

    def handle(self, *args, **options):
        self.stdout.write("Starting demo data population...")

        # 1. Get or Create User
        # Using existing 'admin' or finding first superuser
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(self.style.ERROR("No superuser found. Please create one first."))
            return
        
        # 2. Company & Site
        company, _ = Company.objects.get_or_create(
            name="ACME Construcciones S.A.",
            defaults={"tax_id": "30-12345678-9"}
        )
        
        site, _ = Site.objects.get_or_create(
            company=company,
            name="Obra Torre Centro – Etapa 2",
            defaults={"city": "CABA"}
        )

        # 3. Sector
        sector_struct, _ = Sector.objects.get_or_create(
            company=company,
            name="Estructura"
        )
        
        # 4. Visit
        visit_date = date(2026, 1, 8)
        visit, created = AuditVisit.objects.get_or_create(
            company=company,
            site=site,
            visit_date=visit_date,
            inspector=user,
            defaults={
                "notes": "Se recorrieron niveles 3 al 8. Se detectaron condiciones inseguras relacionadas a orden y limpieza y uso de EPP. Se deja plan de acción con responsables."
            }
        )
        if created:
            self.stdout.write(f"Created Visit: {visit}")
        else:
            self.stdout.write(f"Visit already exists: {visit}")

        # 5. Incident
        # Check if already exists to avoid duplicates on re-run
        if Incident.objects.filter(visit=visit, incident_number=17).exists():
            self.stdout.write("Incident #17 already exists. Skipping creation.")
            incident = Incident.objects.get(visit=visit, incident_number=17)
        else:
            incident = Incident.objects.create(
                visit=visit,
                investigation_date=date(2026, 1, 8),
                incident_number=17,
                incident_date=date(2026, 1, 8),
                incident_time=time(9, 35),
                incident_type=Incident.IncidentType.UNSAFE_CONDITION,
                sector=sector_struct,
                sector_text="Losa nivel 6 – Frente norte", # Even if sector is set, preserving text as requested
                task_performed="Armado de encofrado y colocación de puntales",
                task_mastery=Incident.TaskMastery.MEDIUM,
                description="Se detecta apertura sin protección perimetral en borde de losa nivel 6. No se encontraba instalada baranda ni red, y el área no estaba señalizada. Personal trabajando a menos de 1 metro del borde durante maniobras de armado.",
                
                # Operator
                operator_name="Juan Pérez",
                operator_sector="Estructura",
                operator_position="Ayudante de obra",
                operator_seniority="6 meses",
                
                # Responsible
                responsible_name="Carlos Gómez",
                responsible_role="Capataz de Estructura",
                
                # Risk & Root Cause
                risk_level=Incident.RiskLevel.HIGH,
                cause_number="C-06",
                why_1="Porque el borde de losa no tenía baranda instalada.",
                why_2="Porque la cuadrilla priorizó avanzar el encofrado antes de montar protecciones colectivas.",
                why_3="Porque no había verificación diaria de protecciones colectivas antes de iniciar tareas.",
                why_4="Porque el procedimiento de inicio de jornada no contempla checklist obligatorio de barandas/redes.",
                why_5="Porque no existe un estándar formalizado y auditado de control de protecciones colectivas por sector.",
                
                # Compliance
                legal_framework_internal="Procedimiento SyH PR-SYH-04: Trabajo en altura / Protecciones colectivas",
                improvement_observation="Implementar checklist de inicio de jornada por sector y registrar evidencia fotográfica de protecciones colectivas instaladas."
            )
            self.stdout.write(f"Created Incident: {incident}")

            # 6. Actions (Only create if incident was just created)
            
            # Immediate Action #1
            Action.objects.create(
                incident=incident,
                action_type=Action.ActionType.IMMEDIATE,
                description="Detener tareas en borde de losa y demarcar área de riesgo con cinta y cartelería.",
                owner_name="Carlos Gómez",
                status=Action.Status.DONE,
                execution_date=date(2026, 1, 8),
                closure_date=date(2026, 1, 8),
                effectiveness_theoretical=Action.Effectiveness.HIGH,
                effectiveness_practical=Action.Effectiveness.HIGH
            )

            # Immediate Action #2
            Action.objects.create(
                incident=incident,
                action_type=Action.ActionType.IMMEDIATE,
                description="Instalar baranda metálica temporal en perímetro del borde (mínimo 1,0m, listón intermedio y zócalo).",
                owner_name="Miguel Ríos (Subcontratista Herrería)",
                status=Action.Status.IN_PROGRESS,
                execution_date=date(2026, 1, 8),
                effectiveness_theoretical=Action.Effectiveness.HIGH,
                effectiveness_practical=Action.Effectiveness.NA
            )

            # Corrective Action #1
            Action.objects.create(
                incident=incident,
                action_type=Action.ActionType.CORRECTIVE,
                description="Crear e implementar checklist obligatorio de protecciones colectivas por sector, firmada por capataz y SyH diariamente.",
                owner_name="Laura Martínez (SyH)",
                status=Action.Status.PENDING,
                effectiveness_theoretical=Action.Effectiveness.HIGH,
                effectiveness_practical=Action.Effectiveness.NA
            )

            # Corrective Action #2
            Action.objects.create(
                incident=incident,
                action_type=Action.ActionType.CORRECTIVE,
                description="Capacitación breve (15 min) a cuadrillas de estructura sobre estándar de barandas/redes y reporte de desvíos.",
                owner_name="Laura Martínez (SyH)",
                status=Action.Status.DONE,
                execution_date=date(2026, 1, 9),
                closure_date=date(2026, 1, 9),
                effectiveness_theoretical=Action.Effectiveness.MEDIUM,
                effectiveness_practical=Action.Effectiveness.MEDIUM
            )

            # Corrective Action #3
            Action.objects.create(
                incident=incident,
                action_type=Action.ActionType.CORRECTIVE,
                description="Auditoría semanal de protecciones colectivas con evidencia fotográfica y plan de cierre de hallazgos.",
                owner_name="Carlos Gómez",
                status=Action.Status.IN_PROGRESS,
                execution_date=date(2026, 1, 12),
                effectiveness_theoretical=Action.Effectiveness.HIGH,
                effectiveness_practical=Action.Effectiveness.NA
            )

            # 7. Attachments (Dummy Files)
            # We create dummy content because we don't have the real .jpg/.pdf files
            
            att1 = IncidentAttachment(incident=incident, caption="Borde de losa nivel 6 sin protección antes de la detención", uploaded_by=user)
            att1.file.save("borde_nos_baranda.txt", ContentFile(b"Dummy content for image placeholder"))
            
            att2 = IncidentAttachment(incident=incident, caption="Área demarcada y tareas detenidas", uploaded_by=user)
            att2.file.save("area_demarcada.txt", ContentFile(b"Dummy content"))

            att3 = IncidentAttachment(incident=incident, caption="Baranda temporal instalada (verificación visual)", uploaded_by=user)
            att3.file.save("baranda_instalada.txt", ContentFile(b"Dummy content"))
            
            att4 = IncidentAttachment(incident=incident, caption="Checklist propuesto para implementación", uploaded_by=user)
            att4.file.save("checklist.txt", ContentFile(b"Dummy content for PDF"))

            self.stdout.write("Attachments created (dummy files).")

        # Bonus: Near Miss Incident
        if not Incident.objects.filter(description__startswith="Autoelevador circuló marcha atrás").exists():
            near_miss = Incident.objects.create(
                visit=visit,
                investigation_date=date(2026, 1, 8),
                incident_date=date(2026, 1, 8),
                incident_time=time(10, 15),
                incident_type=Incident.IncidentType.NEAR_MISS,
                sector_text="Depósito / Logística",
                task_performed="Movimiento de materiales con autoelevador",
                task_mastery=Incident.TaskMastery.HIGH,
                description="Autoelevador circuló marcha atrás sin señal acústica; peatón debió apartarse.",
                risk_level=Incident.RiskLevel.MEDIUM,
                why_1="Falla en la alarma de retroceso.",
                why_2="Falta de mantenimiento preventivo.",
            )
            
            Action.objects.create(
                incident=near_miss,
                action_type=Action.ActionType.IMMEDIATE,
                description="Retirar equipo de servicio hasta reparación de alarma.",
                owner_name="Jefe de Taller",
                status=Action.Status.DONE,
                execution_date=date(2026, 1, 8),
                closure_date=date(2026, 1, 8)
            )
            
            Action.objects.create(
                incident=near_miss,
                action_type=Action.ActionType.CORRECTIVE,
                description="Checklist diario pre-uso + demarcación de pasillos peatonales.",
                owner_name="Gerente Logística",
                status=Action.Status.IN_PROGRESS
            )
            self.stdout.write("Created Bonus Near Miss Incident.")
        else:
             self.stdout.write("Bonus Near Miss already exists.")

        self.stdout.write(self.style.SUCCESS("Demo data population completed successfully."))
