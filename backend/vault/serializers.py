from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .encryption import decrypt_text, encrypt_text
from .models import Nominee, ReleaseEvent, Secret, UserProfile


class HeartbeatTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get(self.username_field, "").strip()
        attrs[self.username_field] = self._resolve_username(identifier)
        data = super().validate(attrs)
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.last_heartbeat = timezone.now()
        if profile.vault_released:
            profile.vault_released = False
            profile.released_at = None
        profile.save(update_fields=["last_heartbeat", "vault_released", "released_at", "updated_at"])
        data["user"] = UserSerializer(self.user).data
        return data

    def _resolve_username(self, identifier):
        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
            if user:
                return user.get_username()

        user = User.objects.filter(username__iexact=identifier).first()
        if user:
            return user.get_username()

        return identifier


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    inactivity_days = serializers.IntegerField(write_only=True, min_value=1, max_value=365, default=30)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password", "inactivity_days"]

    def validate_email(self, value):
        value = value.strip().lower()
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Username cannot be blank.")
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def create(self, validated_data):
        inactivity_days = validated_data.pop("inactivity_days", 30)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        UserProfile.objects.get_or_create(user=user, defaults={"inactivity_days": inactivity_days})
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    days_until_release = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "last_heartbeat",
            "inactivity_days",
            "vault_released",
            "released_at",
            "days_until_release",
        ]
        read_only_fields = ["last_heartbeat", "vault_released", "released_at", "days_until_release"]

    def get_days_until_release(self, obj):
        elapsed = timezone.now() - obj.last_heartbeat
        remaining = obj.inactivity_days - elapsed.days
        return max(0, remaining)


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]


class SecretSerializer(serializers.ModelSerializer):
    content = serializers.CharField(write_only=True)

    class Meta:
        model = Secret
        fields = ["id", "title", "category", "content", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["content"] = decrypt_text(instance.encrypted_content)
        return data

    def create(self, validated_data):
        content = validated_data.pop("content")
        return Secret.objects.create(
            encrypted_content=encrypt_text(content),
            **validated_data,
        )

    def update(self, instance, validated_data):
        content = validated_data.pop("content", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if content is not None:
            instance.encrypted_content = encrypt_text(content)
        instance.save()
        return instance


class NomineeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nominee
        fields = ["id", "name", "email", "relationship", "is_verified", "created_at"]
        read_only_fields = ["id", "is_verified", "created_at"]


class ReleaseEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReleaseEvent
        fields = ["id", "triggered_at", "nominee_count", "secret_count", "reason"]
