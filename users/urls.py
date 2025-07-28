from django.urls import path
from users.serializers import RegisterView
from users.views import protected_view, verify_email, PasswordResetRequestView, PasswordResetConfirmView


urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/protected/', protected_view, name='protected'),
    path('api/verify-email/', verify_email, name='email-verify'),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
]