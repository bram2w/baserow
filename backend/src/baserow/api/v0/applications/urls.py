from django.conf.urls import url

from .views import ApplicationsView, ApplicationView


app_name = 'baserow.api.v0.group'

urlpatterns = [
    url(r'group/(?P<group_id>[0-9]+)/$', ApplicationsView.as_view(), name='list'),
    url(r'(?P<application_id>[0-9]+)/$', ApplicationView.as_view(), name='item'),
]
