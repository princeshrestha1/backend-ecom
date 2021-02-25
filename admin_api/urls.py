from django.conf.urls import url
from .views import *

urlpatterns = [
    url('add/products/$', AddProductsAPIView.as_view(), name='addProducts'),
    url('get/products/$', GetProductAPIView.as_view(), name='getProducts'),
]