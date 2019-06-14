from django.urls import path, include
from django.conf.urls import url

from rest_framework import routers
from rest_framework_jwt.views import obtain_jwt_token


router = routers.DefaultRouter()


urlpatterns = [
    url(r'^api/token-auth/', obtain_jwt_token),
    path('api/', include(router.urls)),
]
