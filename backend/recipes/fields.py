import base64
import binascii
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                name = f'{uuid.uuid4()}.{ext}'
                data = ContentFile(base64.b64decode(imgstr), name=name)
            except (ValueError, binascii.Error):
                raise serializers.ValidationError(
                    'Некорректные данные изображения (Base-64).'
                )
        return super().to_internal_value(data)
