from django.conf.urls import url

from .views import ViewsView, ViewView


app_name = 'baserow.contrib.api.v0.views'

urlpatterns = [
    url(r'table/(?P<table_id>[0-9]+)/$', ViewsView.as_view(), name='list'),
    url(r'(?P<view_id>[0-9]+)/$', ViewView.as_view(), name='item'),
]
