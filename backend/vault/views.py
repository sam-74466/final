from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .encryption import decrypt_text
from .models import Nominee, ReleaseEvent, Secret, UserProfile
from .serializers import (
    HeartbeatTokenObtainPairSerializer,
    NomineeSerializer,
    RegisterSerializer,
    ReleaseEventSerializer,
    SecretSerializer,
    UserProfileSerializer,
    UserSerializer,
)
from .services import release_vault_for_profile


class BackendStatusView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "name": "Digital Inheritance Vault API",
                "status": "online",
                "frontend": "http://127.0.0.1:5174",
                "endpoints": {
                    "api_info": "/api/",
                    "health": "/api/health/",
                    "register": "/api/register/",
                    "login": "/api/token/",
                    "admin_data": "/api/admin-data/",
                    "admin": "/admin/",
                },
            }
        )


class HealthView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class HeartbeatTokenObtainPairView(TokenObtainPairView):
    serializer_class = HeartbeatTokenObtainPairSerializer


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": UserSerializer(user).data,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(APIView):
    def get(self, request):
        UserProfile.objects.get_or_create(user=request.user)
        return Response(UserSerializer(request.user).data)


class DashboardView(APIView):
    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        release_events = ReleaseEvent.objects.filter(owner=request.user)[:5]
        elapsed = timezone.now() - profile.last_heartbeat
        deadline = profile.last_heartbeat + timedelta(days=profile.inactivity_days)

        return Response(
            {
                "user": UserSerializer(request.user).data,
                "stats": {
                    "secret_count": Secret.objects.filter(owner=request.user).count(),
                    "nominee_count": Nominee.objects.filter(owner=request.user).count(),
                    "release_count": ReleaseEvent.objects.filter(owner=request.user).count(),
                    "inactive_days": max(0, elapsed.days),
                    "release_deadline": deadline,
                },
                "recent_events": ReleaseEventSerializer(release_events, many=True).data,
            }
        )


class ProfileView(APIView):
    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class HeartbeatView(APIView):
    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.last_heartbeat = timezone.now()
        if profile.vault_released:
            profile.vault_released = False
            profile.released_at = None
        profile.save(update_fields=["last_heartbeat", "vault_released", "released_at", "updated_at"])
        return Response(
            {
                "message": "Heartbeat received. Vault remains active.",
                "profile": UserProfileSerializer(profile).data,
            }
        )


class SimulateInactivityView(APIView):
    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        days = int(request.data.get("days", profile.inactivity_days + 1))
        profile.last_heartbeat = timezone.now() - timedelta(days=max(days, 1))
        profile.vault_released = False
        profile.released_at = None
        profile.save(update_fields=["last_heartbeat", "vault_released", "released_at", "updated_at"])
        return Response(
            {
                "message": f"Demo mode: heartbeat moved back by {days} day(s).",
                "profile": UserProfileSerializer(profile).data,
            }
        )


class CheckInactivityView(APIView):
    def post(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        result = release_vault_for_profile(profile)
        result["username"] = request.user.username
        results = [result]
        return Response(
            {
                "message": "Inactivity check completed.",
                "checked_count": len(results),
                "released_count": len([item for item in results if item["released"]]),
                "emails_sent": sum(item["emails_sent"] for item in results),
                "results": results,
            }
        )


class AdminDataView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        profiles = UserProfile.objects.select_related("user").all()
        secrets = Secret.objects.select_related("owner").all()
        nominees = Nominee.objects.select_related("owner").all()
        release_events = ReleaseEvent.objects.select_related("owner").all()

        return Response(
            {
                "profiles": [
                    {
                        "username": profile.user.username,
                        "email": profile.user.email,
                        "last_heartbeat": profile.last_heartbeat,
                        "inactivity_days": profile.inactivity_days,
                        "vault_released": profile.vault_released,
                        "released_at": profile.released_at,
                    }
                    for profile in profiles
                ],
                "secrets": [
                    {
                        "id": secret.id,
                        "owner": secret.owner.username,
                        "title": secret.title,
                        "category": secret.category,
                        "encrypted_content": secret.encrypted_content,
                        "decrypted_content": _safe_decrypt(secret),
                        "updated_at": secret.updated_at,
                    }
                    for secret in secrets
                ],
                "nominees": [
                    {
                        "id": nominee.id,
                        "owner": nominee.owner.username,
                        "name": nominee.name,
                        "email": nominee.email,
                        "relationship": nominee.relationship,
                        "is_verified": nominee.is_verified,
                    }
                    for nominee in nominees
                ],
                "release_events": [
                    {
                        "id": event.id,
                        "owner": event.owner.username,
                        "triggered_at": event.triggered_at,
                        "nominee_count": event.nominee_count,
                        "secret_count": event.secret_count,
                        "reason": event.reason,
                    }
                    for event in release_events
                ],
            }
        )


class SecretViewSet(viewsets.ModelViewSet):
    serializer_class = SecretSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Secret.objects.all()
        return Secret.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        return Response(
            [
                {"value": value, "label": label}
                for value, label in Secret.CATEGORY_CHOICES
            ]
        )


class NomineeViewSet(viewsets.ModelViewSet):
    serializer_class = NomineeSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Nominee.objects.all()
        return Nominee.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ReleaseEventViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReleaseEventSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return ReleaseEvent.objects.all().annotate(secrets=Count("owner__secrets"))
        return ReleaseEvent.objects.filter(owner=self.request.user).annotate(
            secrets=Count("owner__secrets")
        )


def _safe_decrypt(secret):
    try:
        return decrypt_text(secret.encrypted_content)
    except Exception:
        return "Unable to decrypt with the current vault key."
