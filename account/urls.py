from .views import *
from django.urls import path

app_name = 'account'

urlpatterns = [
    path('', GaavaFrontend.as_view(), name="test"),
    path('accounts/adminlogin/', LoginPage.as_view(), name='adminlogin'),
    path('accounts/adminlogout/', LogoutPage.as_view(), name='adminlogout'),
    path('gaava-admin/', GaavaBackend.as_view(), name="breadfruit_admin"),
    path('accounts/register/', RegistrationView.as_view(), name="registration"),
    path('accounts/login/', ClientLoginView.as_view(), name="client_login"),
    path('accounts/logout/', LogoutView.as_view(), name="logout"),
    path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
        activate, name="activate"),
    path('accounts/deactivate/', Deactivate.as_view(), name="deactivate"),

    path('accounts/profile/<int:pk>/edit/', ProfileUpdateView.as_view(),
        name="profile-edit"),
    path('accounts/profile/<int:pk>/detail/', ProfileDetailView.as_view(),
        name="profile-detail"),
    path('update-shipping-address/', UpdateShippingAddress.as_view(),
        name="update_shipping_addr"),

    path('accounts/staff/list/',
        AdminStaffListView.as_view(), name='adminStaffList'),
    path('accounts/staff/create/',
        AdminStaffCreateView.as_view(), name='adminStaffCreate'),
    path('accounts/staff/<int:pk>/update/',
        AdminStaffUpdateView.as_view(), name="adminStaffUpdate"),
    path('account/staff/<int:pk>/delete/',
        AdminStaffDeleteView.as_view(), name="adminStaffDelete"),

    path('subscribe/', SubscriberCreate.as_view(), name='subcriber'),
    path('email/confirmation/', EmailConfirmation.as_view(), name='email_confirmation'),
    path('subscribe-list/', SubscribersListView.as_view(), name='subcriber_list'),
    path('subscriber/<int:pk>/delete/',SubscriberDeleteView.as_view(), name='subscriber_delete'),
    path('subscribe-list/csv/', ExportSubscriberCSV.as_view(), name="subscribers_in_csv"),
    path('password/reset/', ResetPasswordRequestView.as_view(),
        name='forget_password'),
    path('password/reset/done/', PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    path('change_password/user/', ChangePassword.as_view(), name='change_password'),
    # path('.*/', BreadFruitFrontend.as_view(), name='test'),
]
