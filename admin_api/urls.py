from django.conf.urls import url
from .views import *

urlpatterns = [
    url('add/products/$', AddProductsAPIView.as_view(), name='addProducts'),
]