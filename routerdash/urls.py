from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dash.views.home', name='home'),
    url(r'^ajax/speeds/$', 'dash.views.ajax_speeds'),
    url(r'^ajax/devices/$', 'dash.views.ajax_devices'),
    url(r'^admin/', include(admin.site.urls)),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
