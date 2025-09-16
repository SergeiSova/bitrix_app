from django.urls import path

from start.views.start import start
from product.api.autocomplete_products import autocomplete_products
from product.views.qr_generator import qr_generator
from product.views.cards import product_card
from product.views.catalog import product_catalog

urlpatterns = [
    path('generator/', qr_generator, name='qr_generator'),
    path('catalog/', product_catalog, name='catalog'),
    path('card/<slug:uuid>/', product_card, name='product_card'),
    path('autocomplete/', autocomplete_products, name='autocomplete'),
    path('',start, name='start')
]