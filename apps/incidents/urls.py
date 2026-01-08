# apps/incidents/urls.py
from django.urls import path
from .views import IncidentListView, IncidentCreateView, IncidentDetailView, IncidentUpdateView, IncidentDetailPDFView

app_name = "incidents"

urlpatterns = [
    path("", IncidentListView.as_view(), name="list"),
    path("new/", IncidentCreateView.as_view(), name="create"),
    path("<int:pk>/", IncidentDetailView.as_view(), name="detail"),
    path("<int:pk>/pdf/", IncidentDetailPDFView.as_view(), name="detail_pdf"),
    path("<int:pk>/edit/", IncidentUpdateView.as_view(), name="update"),
]
