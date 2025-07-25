from django.urls import path
from users.serializers import RegisterView
from users.views import protected_view


urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/protected/', protected_view, name='protected'),
]