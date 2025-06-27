import base64
import binascii
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers
from PIL import Image, UnidentifiedImageError


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                fmt, imgstr = data.split(';base64,')
            except ValueError:
                raise serializers.ValidationError('Некорректный data-URL.')

            try:
                decoded = base64.b64decode(imgstr)
            except binascii.Error:
                raise serializers.ValidationError(
                    'Не удалось декодировать base64.')

            ext = fmt.split('/')[-1]
            data = ContentFile(decoded, name=f'{uuid.uuid4()}.{ext}')

            try:
                Image.open(data).verify()
                data.file.seek(0)
            except (UnidentifiedImageError, OSError):
                raise serializers.ValidationError(
                    'Файл не является изображением.')

        return super().to_internal_value(data)
