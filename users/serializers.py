from django.contrib.auth.models import User
from rest_framework import serializers, generics
from django.contrib.auth import get_user_model
from .models import PasswordResetToken

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email.")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_token(self, value):
        try:
            self.token_obj = PasswordResetToken.objects.get(token=value)
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError("Invalid token.")
        if self.token_obj.is_expired():
            self.token_obj.delete()
            raise serializers.ValidationError("Token expired.")
        return value

    def save(self):
        user = self.token_obj.user
        user.set_password(self.validated_data['new_password'])
        user.save()
        self.token_obj.delete()
        return user
