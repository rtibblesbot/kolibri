from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated

from kolibri.core.api import ValuesViewset
from kolibri.core.serializers import HexOnlyUUIDField

from ..models import PinnedDevice


class PinnedDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for handling requests regarding a user's Pinned Devices
    """

    instance_id = HexOnlyUUIDField()

    class Meta:
        model = PinnedDevice
        fields = ("instance_id", "id")


class PinnedDeviceViewSet(ValuesViewset):
    serializer_class = PinnedDeviceSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return PinnedDevice.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
