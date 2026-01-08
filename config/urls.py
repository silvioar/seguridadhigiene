"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from core.views import (
    DashboardView, DashboardPDFView,
    CompanyCreateView, SiteCreateView, SectorCreateView
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("audits/", include("audits.urls")),
    path("", DashboardView.as_view(), name="dashboard"),
    path("dashboard/pdf/", DashboardPDFView.as_view(), name="dashboard_pdf"),
    
    # Quick Add Views
    path("companies/new/", CompanyCreateView.as_view(), name="company_create"),
    path("sites/new/", SiteCreateView.as_view(), name="site_create"),
    path("sectors/new/", SectorCreateView.as_view(), name="sector_create"),

    path("incidents/", include("incidents.urls")),
]
