from django.conf.urls import url

from .views import GroupsView, GroupView, GroupOrderView


app_name = 'baserow.api.v0.group'

urlpatterns = [
    url(r'^$', GroupsView.as_view(), name='list'),
    url(r'(?P<group_id>[0-9]+)/$', GroupView.as_view(), name='item'),
    url(r'order/$', GroupOrderView.as_view(), name='order')
]
