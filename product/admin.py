from django.contrib import admin
from .models import QRLink

@admin.register(QRLink)
class ProductLinksAdmin(admin.ModelAdmin):
    list_display = ("product_id", "unique_id", "created_at")