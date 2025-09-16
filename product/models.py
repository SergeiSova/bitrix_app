import uuid
from django.db import models

class QRLink(models.Model):
    product_id = models.PositiveIntegerField(verbose_name="Product ID")
    unique_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, verbose_name="Token")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created at")

    class Meta:
        verbose_name = "QR-ссылка товара"
        verbose_name_plural = "QR-ссылки товаров"
