from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import RedirectView

from company.views.company_map import company_map
from contacts.api.autocomplete_companies import autocomplete_companies
from contacts.views.export_contacts import export_contacts
from contacts.views.import_contacts import import_contacts
from staff.views.employees import employees_telephony
from staff.views.telephony import call_generator


def redirect_to(pattern_name):
    return xframe_options_exempt(RedirectView.as_view(pattern_name=pattern_name, query_string=True))


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('deals.urls')),
    path('product/', include('product.urls')),
    path('generator/', redirect_to('qr_generator')),
    path('telephony/', employees_telephony, name='telephony'),
    path('telephony/generate/', call_generator, name='call_generator'),
    path('staff/', redirect_to('telephony')),
    path('company_map/', company_map, name='company_map'),
    path('company/', redirect_to('company_map')),
    path('contacts/', redirect_to('import_contacts')),
    path('contacts/import/', import_contacts, name='import_contacts'),
    path('contacts/export/', export_contacts, name='export_contacts'),
    path('contacts/autocomplete', autocomplete_companies, name='autocomplete_companies'),
    path('import/', redirect_to('import_contacts')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
