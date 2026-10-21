from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminDataView,
    BackendStatusView,
    CheckInactivityView,
    DashboardView,
    HeartbeatView,
    HealthView,
    MeView,
    NomineeViewSet,
    ProfileView,
    RegisterView,
    ReleaseEventViewSet,
    SecretViewSet,
    SimulateInactivityView,
)

router = DefaultRouter()
router.register("secrets", SecretViewSet, basename="secret")
router.register("nominees", NomineeViewSet, basename="nominee")
router.register("release-events", ReleaseEventViewSet, basename="release-event")

urlpatterns = [
    path("", BackendStatusView.as_view(), name="api-info"),
    path("health/", HealthView.as_view(), name="health"),
    path("admin-data/", AdminDataView.as_view(), name="admin-data"),
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("heartbeat/", HeartbeatView.as_view(), name="heartbeat"),
    path("simulate-inactivity/", SimulateInactivityView.as_view(), name="simulate-inactivity"),
    path("check-inactivity/", CheckInactivityView.as_view(), name="check-inactivity"),
]
