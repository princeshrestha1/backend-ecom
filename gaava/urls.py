"""gaava URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from account.views import (
    CustomerPasswordResetConfirmView, CustomerPasswordResetCompleteView)
from django.views.generic import RedirectView



# handler404 = handler404

urlpatterns = [
    # path('', include('account.urls'), name='account'),
    # path('', include('cart.urls'), name='cart'),
    path('super/admin/', admin.site.urls),
    # path('messages/', include('messaging.urls')),
    # path('reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
    #     CustomerPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('reset/done/', CustomerPasswordResetCompleteView.as_view(),
    #     name='password_reset_complete'),
    
    # path('oauth/', include('social_django.urls'), name='social'),
    # path('inbox/notifications/', include('notifications.urls'), name='notifications'), 
    # path('apis/', include('shop_api.urls')),
    path('api/v1/', include('api.urls')),
    # path('rest-auth/', include('rest_auth.urls'), name='rest_auth'),

    # path('ckeditor/', include('ckeditor_uploader.urls')),
    
    path('admin/', include('admin_api.urls')),
]


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

