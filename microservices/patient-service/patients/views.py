from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.db import connection

class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({{'status': 'healthy'}}, status=status.HTTP_200_OK)

class ReadinessCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            connection.ensure_connection()
            return Response({{'status': 'ready'}}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {{'status': 'not ready', 'error': str(e)}},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
