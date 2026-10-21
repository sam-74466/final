from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import Secret, UserProfile


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class VaultFlowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_public_backend_status_endpoints_are_browsable(self):
        root_response = self.client.get("/")
        api_response = self.client.get("/api/")
        health_response = self.client.get("/api/health/")

        self.assertEqual(root_response.status_code, 200)
        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(health_response.status_code, 200)
        self.assertEqual(health_response.data["status"], "ok")

    def test_admin_data_requires_staff_access(self):
        anonymous_response = self.client.get("/api/admin-data/")
        self.assertEqual(anonymous_response.status_code, 403)

        admin = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="AdminPass123",
        )
        self.client.force_authenticate(user=admin)
        staff_response = self.client.get("/api/admin-data/")
        self.assertEqual(staff_response.status_code, 200)
        self.assertIn("profiles", staff_response.data)

    def test_register_then_login_returns_tokens_and_profile(self):
        register_response = self.client.post(
            "/api/register/",
            {
                "username": " auth_user ",
                "email": " Auth_User@Example.com ",
                "password": "strong-pass-123",
                "inactivity_days": 14,
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, 201)
        self.assertIn("access", register_response.data)
        self.assertEqual(register_response.data["user"]["username"], "auth_user")
        self.assertEqual(register_response.data["user"]["email"], "auth_user@example.com")
        self.assertEqual(register_response.data["user"]["profile"]["inactivity_days"], 14)

        login_response = self.client.post(
            "/api/token/",
            {
                "username": " AUTH_USER@EXAMPLE.COM ",
                "password": "strong-pass-123",
            },
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access", login_response.data)
        self.assertEqual(login_response.data["user"]["username"], "auth_user")

    def test_full_vault_release_flow(self):
        register_response = self.client.post(
            "/api/register/",
            {
                "username": "demo_owner",
                "email": "owner@example.com",
                "password": "strong-pass-123",
                "inactivity_days": 1,
            },
            format="json",
        )
        self.assertEqual(register_response.status_code, 201)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {register_response.data['access']}")

        secret_response = self.client.post(
            "/api/secrets/",
            {
                "title": "Recovery phrase",
                "category": "recovery",
                "content": "keep this private",
            },
            format="json",
        )
        self.assertEqual(secret_response.status_code, 201)
        stored_secret = Secret.objects.get(title="Recovery phrase")
        self.assertNotIn("keep this private", stored_secret.encrypted_content)

        nominee_response = self.client.post(
            "/api/nominees/",
            {
                "name": "Asha Mehta",
                "email": "asha@example.com",
                "relationship": "Sister",
            },
            format="json",
        )
        self.assertEqual(nominee_response.status_code, 201)

        self.client.post("/api/simulate-inactivity/", {"days": 2}, format="json")
        check_response = self.client.post("/api/check-inactivity/", {}, format="json")
        self.assertEqual(check_response.status_code, 200)
        self.assertEqual(check_response.data["checked_count"], 1)
        self.assertEqual(check_response.data["released_count"], 1)
        self.assertEqual(check_response.data["emails_sent"], 1)
        self.assertEqual(check_response.data["results"][0]["username"], "demo_owner")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("keep this private", mail.outbox[0].body)

        profile = UserProfile.objects.get(user__username="demo_owner")
        self.assertTrue(profile.vault_released)

        repeat_response = self.client.post("/api/check-inactivity/", {}, format="json")
        self.assertEqual(repeat_response.status_code, 200)
        self.assertEqual(repeat_response.data["released_count"], 0)
        self.assertEqual(repeat_response.data["results"][0]["reason"], "Vault was already released.")
