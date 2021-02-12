from django.contrib import admin
from .models import Subscriber, User, ShippingAddress

admin.site.register(Subscriber)
admin.site.register(User)
admin.site.register(ShippingAddress)
