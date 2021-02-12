from django.conf.urls import url
from rest_framework_swagger.views import get_swagger_view

from shop_api.views import *

schema_view = get_swagger_view(title='Breadfruit API')

urlpatterns = [
    url(r'^$', schema_view),
    url(r'^login/$', UserLoginAPIView.as_view(), name='login'),
    url(r'^account/register/$', UserRegisterAPIView.as_view(), name='register'),
    url(r'^profile-edit/$', UserUpdateAPIView.as_view(), name='profile_edit'),
    url(r'^update-address/$', UserUpdateBillingAddressAPIView.as_view(), name='update_address'),
    url(r'^change-password/$', ChangePasswordAPIView.as_view(), name='change_password'),

    url(r'^products/$', ProductList.as_view(), name='products'),
    url(r'^products/walnut$', ProductListWalnut.as_view(), name='products_walnut'),
    url(r'^similar-product/(?P<prod_id>\d+)/$', SimilarProductList.as_view(), name="similar_product"),

    url(r'^sorted/products/(?P<cat_id>\d+)/$', SortedProductList.as_view(), name='sorted-products'),
    url(r'^sorted/by/rating/$', RatingWiseSortingAPI.as_view(), name='sorted-by-rating'),

    url(r'^categories/$', CategoryList.as_view(), name='categories'),
    url(r'^wishlist-products/$', ProductsInWishlist.as_view(), name='wishlist_products'),
    url(r'^cart-products/$', ProductsInCart.as_view(), name='cart_products'),
    url(r'^cart-item-count/$', CountCartItemAPI.as_view(), name="cart_item_count"),
    url(r'^latest-products/$', LatestProducts.as_view(), name='latest_products'),
    url(r'^comingsoon-products/$', ComingSoonProducts.as_view(), name='coming_products'),
    url(r'^onsale-products/$', OnSaleProducts.as_view(), name='onsale_products'),
    url(r'^featured-products/$', FeaturedProducts.as_view(), name='featured_products'),
    url(r'^sliders/$', SliderList.as_view(), name='sliders'),
    url(r'^product/(?P<pk>\d+)/detail/$', ProductDetail.as_view(), name='product_detail'),
    url(r'^quantity/(?P<pk>\d+)/update/$', UpdateQuantityAPIView.as_view(), name='update_quantity'),

    url(r'^search/(?P<cat_id>\d+)/category/$', SearchByCategoryAPI.as_view(), name='search_category'),
    url(r'^category/(?P<cat_id>\d+)/products/$', ProductByCategoryAPI.as_view(), name='category_products'),
    url(r'^search/$', SearchByValueAPI.as_view(), name='search'),
    url(r'^select/multiple/categories/$', SearchWithMultipleCategories.as_view(), name='sel_mul_cat'),


    url(r'^addto/cart/(?P<prod_id>\d+)/$', AddToCart.as_view(), name="in-cart"),   
    url(r'^remove/from/cart/(?P<cart_id>\d+)/$',RemoveFromCart.as_view(), name="remove_from_cart"),
    url(r'^addto/wish-list/(?P<prod_id>\d+)/$', AddToWishList.as_view(), name="to-wish_list"),
    url(r'^notify-me/(?P<prod_id>\d+)/$', NotifyMeCreateAPI.as_view(), name="notify_me"),

    url(r'^my/orders/$', MyOrders.as_view(), name='my-orders'),
    url(r'^order/(?P<order_id>\d+)/detail/$', OrderDetailAPI.as_view(), name='order_detail'),         

    url(r'^my/coupons/$', CouponListAPI.as_view(), name='my-coupons'),
    url(r'^coupon/(?P<pk>\d+)/detail/$', CouponDetailAPI.as_view(), name='coupon_detail'),         

    url(r'^checkout/$', Checkout.as_view(), name='checkout'),  
    url(r'^confirm/order/$', ConfirmOrder.as_view(), name='confirm-order'),
    url(r'^apply-coupon/$', ApplyCoupon.as_view(), name='apply_coupon'),
    url(r'^confirm/order/(?P<coupon_id>\d+)/$', ConfirmOrderWithCoupon.as_view(),
        name='confirm_order_with_coupon'),

    url(r'^notifications/$', NotificationsListAPI.as_view(), name="notifications"),

    url(r'^ordered/products/$', ProductFromOrder.as_view(), name="ordered_product"),
    url(r'^individual/product/order/(?P<prod_id>\d+)/$', IndividualProductOrderView.as_view(), name="ind_ordered_product"),
    url(r'^individual/product/order/(?P<order_id>\d+)/detail/$', IndividualProductOrderDetailView.as_view(), name="ind_ordered_product_detail"),
    url(r'^create-rate/(?P<prod_id>\d+)/$', ReviewCreateAPI.as_view(), name="create_rate"),

    url(r'^buy/now/(?P<prod_id>\d+)/$', BuyNowAPI.as_view(), name="buy_now"),
    # url(r'^confirm/checkout/$', ConfirmCheckoutAPI.as_view(), name="confirm_checkout"),

    # url(r'^share/(?P<prod_id>\d+)/$', ShareAPI.as_view(), name="share"),
    url(r'^user-address/$', UserCurrentAddress.as_view(), name="user_address"),
    url(r'^recently-viewed/$', RecentlyViewedProducts.as_view(), name="recently_viewed"),
    url(r'^product-in-transaction/(?P<product_id>\d+)/update/(?P<quantity>\d+)', UpdateProductInTransaction.as_view(), name='update_product_transaction'),
    url(r'^product-in-transaction/list/', ProductInTransactionListView.as_view(), name='product_transaction'),

    # url(r'^updatestocks/',StockUpdateFromWalnut.as_view()),
    url(r'^stockcheck/',StockCheckFromWalnut.as_view()),
    url(r'^stockcheckrefund/',StockCheckFromWalnutRefund.as_view()),

]
