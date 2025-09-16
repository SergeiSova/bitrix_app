from django.urls import path

from deals.views.active_deals import active_deals
from deals.views.add_deal import add_deal
from start.views.start import start

urlpatterns = [
    path('', start, name='home'),
    path('start/', start, name='start'),
    path('deals/', active_deals, name='deals'),
    path('add/', add_deal, name='add_deal')
]
