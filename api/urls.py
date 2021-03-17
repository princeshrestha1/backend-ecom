from django.conf.urls import url
from rest_framework_swagger.views import get_swagger_view
from api.views import *
# from rest_framework_simplejwt import views as jwt_views

schema_view = get_swagger_view(title='gaavaa API')
urlpatterns = [
    url(r'^$', schema_view),
    url(r'^account/register/$', UserRegisterAPIView.as_view(), name='register'),
    url(r'^account/verify/$', UserVerifyAPIView.as_view(), name='register'),
    url(r'^account/login/$', UserLoginAPIView.as_view(), name='login'),
    url(r'^profile-edit/$', UserUpdateAPIView.as_view(), name='profile_edit'),
    url(r'^add-address/$', UserUpdateBillingAddressAPIView.as_view(), name='update_address'),
    url(r'^update-address/$', UpdateBillingAddressAPIView.as_view(), name='update_address'),
    url(r'^get-address/$', GetUserShippingAddress.as_view(), name='get_address'),
    url(r'^logout/$', LogoutAPIView.as_view(), name='Logout'),

    url(r'^products-list/$', ProductList.as_view(), name='products'),
    url(r'^category-list/$', CategoryList.as_view(), name='categories'),
    url(r'^singleproduct-list/$', SingleProductAPIView.as_view(), name='product'),
    url(r'^usercart-list/$', CartListAPIView.as_view(), name='cart_list'),
    url(r'^addproductto-cart/$', AddProducttoCart.as_view(), name='addItems'),
    url(r'^abortproduct-list/$', CancelListAPIView.as_view(), name='increase_cart_items'),
    url(r'^myorders-list/$', OnProgressListAPIView.as_view(), name='increase_cart_items'),
    url(r'^recentorder-list/$', RecentProductAPIView.as_view(), name='increase_cart_items'),
    url(r'^home/$', HomeView.as_view(), name='home'),
    url(r'^checkout/$', CheckoutAPIView.as_view(), name='checkout'),
    url(r'^addproductcount/$', AddProductCountAPIView.as_view(), name='add_count'),
    url(r'^cancelorder/$', CancelOrderAPIView.as_view(), name='add_count'),
    url(r'^removeproductcount/$', RemoveProductCountAPIView.as_view(), name='remove_count'),
    url(r'^recent-orders/$', GetPreviousOrderAPIView.as_view(), name='remove_count'),
    url(r'^confirm-checkout/$', ConfirmCheckoutAPIView.as_view(), name='remove_count'),
    url(r'^order-summary/$', OrderSummaryAPIView.as_view(), name='order_summary'),

    url(r'^get/similarproducts/$', GetSimilarProductsAPIView.as_view(), name='getSimilarProducts'),
    url(r'^get/productsbytags/$', GetProductByTags.as_view(), name='getSimilarProducts'),
    url(r'^get/ads/$', GetADSAPIView.as_view(), name='GetADSAPIView'),
    ]
