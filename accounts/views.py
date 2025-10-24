from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets

from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
	queryset = get_user_model().objects.all().order_by("id")
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAdminUser]
	filterset_fields = ["is_active", "is_staff"]
	search_fields = ["username", "email", "first_name", "last_name"]
	ordering_fields = ["id", "username", "date_joined"]
