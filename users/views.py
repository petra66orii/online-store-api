from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from datetime import timedelta, datetime
from django.views.decorators.csrf import csrf_exempt
from .models import PasswordResetToken
from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from django.contrib.auth import get_user_model

User = get_user_model()

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({'message': f'Hello, {request.user.username}!'})

@csrf_exempt
@api_view(['POST'])
def register_user(request):
    data = request.data
    if User.objects.filter(username=data['username']).exists():
        return Response({'detail': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        is_active=False
    )

    token = AccessToken.for_user(user)
    token.set_exp(lifetime=timedelta(hours=24))  # Default is 5 minutes

    token = RefreshToken.for_user(user).access_token
    verify_url = request.build_absolute_uri(
        reverse('email-verify') + f'?token={str(token)}'
    )

    # Render HTML email
    subject = 'Verify your email'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [user.email]
    text_content = f'Click the link to verify your email: {verify_url}'
    html_content = render_to_string('emails/verify_email.html', {'username': user.username, 'verify_url': verify_url})

    email = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    email.attach_alternative(html_content, "text/html")
    email.send()

    return Response({'detail': 'User created. Check your email to verify account.'})


@api_view(['GET'])
def verify_email(request):
    token = request.GET.get('token')
    try:
        access_token = AccessToken(token)
        user_id = access_token['user_id']
        user = User.objects.get(id=user_id)
        if not user.is_active:
            user.is_active = True
            user.save()
        return Response({'detail': 'Email verified successfully'})
    except Exception:
        return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def resend_verification_email(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        if user.is_active:
            return Response({'detail': 'Account already verified'})

        token = RefreshToken.for_user(user).access_token
        verify_url = request.build_absolute_uri(
            reverse('email-verify') + f'?token={str(token)}'
        )
        send_mail(
            'Verify your email',
            f'Click the link to verify: {verify_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        return Response({'detail': 'Verification email resent'})
    except User.DoesNotExist:
        return Response({'detail': 'User not found'}, status=404)


class PasswordResetRequestView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(email=serializer.validated_data['email'])

        # Delete old tokens
        PasswordResetToken.objects.filter(user=user).delete()

        token_obj = PasswordResetToken.objects.create(user=user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token_obj.token}"

        subject = "Reset Your Password"
        from_email = "noreply@example.com"
        to = user.email

        html_content = render_to_string("emails/password_reset.html", {
            "reset_link": reset_link,
            "year": datetime.datetime.now().year,
        })
        text_content = f"Reset your password: {reset_link}"

        email = EmailMultiAlternatives(subject, text_content, from_email, [to])
        email.attach_alternative(html_content, "text/html")
        email.send()

        return Response({"detail": "Password reset link sent."}, status=200)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password successfully reset."}, status=200)