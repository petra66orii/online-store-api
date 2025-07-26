from django.urls import path
from users.serializers import RegisterView
from users.views import protected_view, verify_email


urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/protected/', protected_view, name='protected'),
    path('api/verify-email/', verify_email, name='email-verify'),

]