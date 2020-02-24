from cycle_2020.models import *
from rest_framework import routers, serializers, viewsets

class FilingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filing
        fields = Filing.export_fields()

class FilingViewSet(viewsets.ModelViewSet):
    serializer_class = FilingSerializer
    queryset = Filing.objects.filter(active=True).order_by('-created')
