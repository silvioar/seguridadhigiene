# apps/audits/urls.py
from django.urls import path
from .views import VisitListView, VisitCreateView, VisitDetailView

app_name = "audits"

urlpatterns = [
    path("", VisitListView.as_view(), name="list"),
    path("new/", VisitCreateView.as_view(), name="create"),
    path("<int:pk>/", VisitDetailView.as_view(), name="detail"),
]
