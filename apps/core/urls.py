from django.urls import path
from .views import (
    DashboardView, DashboardPDFView,
    CompanyCreateView, SiteCreateView, SectorCreateView
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("dashboard/pdf/", DashboardPDFView.as_view(), name="dashboard_pdf"),
    
    # Quick creation urls
    path("companies/new/", CompanyCreateView.as_view(), name="company_create"),
    path("sites/new/", SiteCreateView.as_view(), name="site_create"),
    path("sectors/new/", SectorCreateView.as_view(), name="sector_create"),
]
