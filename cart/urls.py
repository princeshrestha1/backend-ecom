from django.urls import path, include
from .views import *
from .views_admin import *
from django.views.generic import TemplateView

app_name = 'cart'

urlpatterns = [
    # path('run/', RunView.as_view(), name='run'),
    # path('robots\.txt', RobotsTemplateView.as_view(), name='robots'),
    # path('gaava-admin/', DashBoard.as_view(), name='dashboard'),
    # path('create-tag/', CreateTagView.as_view(), name='create_tag'),
    # path('create-status/', CreateStatusView.as_view(), name='create_status'),
    # path('search/', SearchResult.as_view(), name="search_result"),
    # path('cart-item-count/', CountCartItem.as_view(), name="cart_item_count"),
    # path('my-cart/', MyCartItem.as_view(), name="my_cart_item"),
    # path('wishlist-item-count/', CountWishListItem.as_view(), name="wishlist_item_count"),
    # path('multiple/option/confirmation/<str:model>/<str:option>/',
    #     MultipleOptionConfirmation.as_view(), name='multiple_option_confirmation'),

    # path('shop/category/create/', CategoryCreateView.as_view(), name="category_create"),
    # path('shop/category/<int:pk>/update/', CategoryUpdateView.as_view(), name="category_update"),
    # path('shop/categories/', CategoryListView.as_view(), name="categories"),
    # path('shop/category/<int:pk>/delete/', CategoryDelete.as_view(), name='category_delete'),
    # path('shop/multiple/category/delete/', MultipleCategoryDeletion.as_view(), name='category_delete_multiple'),

    # path('shop/coupon/create/', CouponCreateView.as_view(), name="coupon_create"),
    # path('shop/coupons/', CouponListView.as_view(), name="coupons"),
    # path('shop/coupon/<int:pk>/update/', CouponUpdateView.as_view(), name='coupon_update'),
    # path('shop/coupon/<int:pk>/delete/', CouponDelete.as_view(), name='coupon_delete'),
    # path('shop/multiple/coupon/delete/', MultipleCouponDeletion.as_view(), name='coupon_delete_multiple'),

    # path('shop/product/create/', ProductCreateView.as_view(), name="product_create"),
    # path('shop/products/', ProductListView.as_view(), name="products"),
    # path('shop/products/csv/', ExportProductCSV.as_view(), name="products_in_csv"),
    # path('shop/product/<int:pk>/update/', ProductUpdateView.as_view(), name='product_update'),
    # path('shop/product/<int:pk>/add/quantity/', AddQuantityAdmin.as_view(), name='add_quantity'),
    # path('shop/product/<int:pk>/preview/', ProductPreview.as_view(), name='product_preview'),    
    # path('shop/product/<int:pk>/delete/', ProductDelete.as_view(), name='product_delete'),
    # path('shop/multiple/product/select/', MultipleProductDeletion.as_view(), name='product_delete_multiple'),
    # path('cover/image/<int:prod_id>/', AssignTitlePhoto.as_view(), name='change_title_photo'),
    # path('export/product/<int:product_id>/', export_product_detail, name='export_product_detail'),
    # path('add/photo/<int:prod_id>/', AddPhoto.as_view(), name='add_photo'),
    # path('products/export/csv/', ExportProductCSV.as_view(), name="products_in_csv"),
    # path('users/export/csv/', ExportUserCSV.as_view(), name="users_in_csv"),



    # path('shop/tag/create/', TagCreateView.as_view(), name="tag_create"),
    # path('shop/tag/<int:pk>/update/', TagUpdateView.as_view(), name="tag_update"),
    # path('shop/tags/', TagListView.as_view(), name="tags"),
    # path('shop/tag/<int:pk>/delete/', TagDeleteView.as_view(), name="tag_delete"),
    # path('shop/multiple/tag/delete/', MultipleTagDeletion.as_view(), name='tag_delete_multiple'),

    # path('shop/keyword/create/', KeywordCreateView.as_view(), name="keyword_create"),
    # path('shop/keyword/<int:pk>/update/', KeywordUpdateView.as_view(), name="keyword_update"),
    # path('shop/keywords/', KeywordListView.as_view(), name="keywords"),
    # path('shop/keyword/<int:pk>/delete/', KeywordDeleteView.as_view(), name="keyword_delete"),
    # path('shop/multiple/keyword/delete/', MultipleKeywordDeletion.as_view(), name='keyword_delete_multiple'),

    # path('shop/slider/create/', SliderCreateView.as_view(), name="slider_create"),
    # path('shop/slider/<int:pk>/update/', SliderUpdateView.as_view(), name="slider_update"),
    # path('shop/sliders/', SliderListView.as_view(), name="sliders"),
    # path('shop/slider/<int:pk>/delete/', SliderDeleteView.as_view(), name="slider_delete"),
    # path('shop/multiple/slider/delete/', MultipleSliderDeletion.as_view(), name='slider_delete_multiple'),

    # path('shop/photos/', PhotoList.as_view(), name="photo_list"),
    # path('shop/photo/<int:pk>/update/', PhotoUpdate.as_view(), name="photo_update"),
    # path('shop/photo/<int:pk>/delete/', PhotoDelete.as_view(), name="photo_delete"),
    # path('remove/image/<int:prod_id>/', DeletePhotos.as_view(), name='delete_photos'),

    # path('shop/siteconfig/create/',
    #     AdminSiteConfigCreateView.as_view(), name="adminSiteConfigCreate"),
    # path('shop/siteconfigs/',
    #     AdminSiteConfigListView.as_view(), name="adminSiteConfigList"),
    # path('shop/siteconfig/<int:pk>/update/',
    #     AdminSiteConfigUpdateView.as_view(), name="adminSiteConfigUpdate"),

    # path('shop/featured_product/create/',
    #     FeaturedProductCreateView.as_view(), name="featured_product_create"),
    # path('shop/featured_product/list/',
    #     FeaturedProductListView.as_view(), name="featured_product_list"),
    # path('shop/featured_product/<int:pk>/update/',
    #     FeaturedProductUpdateView.as_view(), name='featured_product_update'),
    # path('shop/featured_product/<int:pk>/delete/',
    #     FeaturedProductDeleteView.as_view(), name='featured_product_delete'), 
    # path('shop/multiple/featured/delete/', MultipleFeaturedProductDeletion.as_view(),
    #     name='featured_prod_delete_multiple'),
    # path('shop/today_deals/<int:pk>',
    #     TodayDeals.as_view(), name="today_deals"),

    # path('shop/users/', UsersListView.as_view(), name="users"),
    # path('shop/user/create/',UserCreateView.as_view(), name="user_create"),
    # path('shop/user/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    # path('shop/user/<int:pk>/delete/', UserDelete.as_view(), name='user_delete'),
    # path('shop/user/<int:pk>/detail', UserDetail.as_view(), name="user_detail"),
    # path('password-reset-user/<int:userId>/',UserPwdResetView.as_view(),
    #     name='password_reset_user_view'),
    # path('export/user/<int:customer_id>/', export_customer_detail, name='export_customer_detail'),

    # path('inquiry-us/', InquiryCreate.as_view(), name="inquiry_us"),
    # path('shop/inquiries/', InquiryListView.as_view(), name="inquiries"),
    # path('shop/inquiry/<int:pk>/detail/', InquiryDetailView.as_view(), name="inquiry_detail"),
    # path('shop/inquiry/<int:pk>/update/', InquiryRespondBack.as_view(), name="inquiry_respond_back"),
    # path('shop/multiple/inquiry/delete/', MultipleInquiryDeletion.as_view(), name='inquiry_delete_multiple'),

    # path('orders/', OrdersListView.as_view(), name="orders"),
    # path('bill/<int:pk>/', BillCreateView.as_view(), name="bill-generate"),

    # path('order/ship/<int:pk>/update/', OrdersUpdateStatusView.as_view(), name="orders"),
    # path('order/<int:pk>/update/', OrdersUpdateView.as_view(), name="orders_update"),
    # path('shop/product/<int:pk1>/order/<int:pk2>/',
    #     OrderProductAdd.as_view(), name="orders_product"),
    # path('order/<int:pk>/refund/', OrderRefundView.as_view(), name="order_refund"),
    # path('order/product/update/quantity/',
    #     OrderProductUpdateQuantityView.as_view(), name="order_product_update_quantity"),
    # path('product/<int:product_id>/order/<int:pk>/delete/', OrderProductDeleteView.as_view(), name="orders_product_delete"),
    # path('shop/order/<int:pk>/detail/', AdminOrderDetailView.as_view(), name="order_details"),
    # path('shop/bill/<int:order_id>/', BillView.as_view(), name="bill"),
    # path('bill/generation/<int:order_id>/', bill_generation, name='bill_generation'),


    # path('order/<int:pk>/confirm/', ConfirmOrderByCMS.as_view(), name="confirm_order_by_cms"),
    # path('search/products/', ProductSearchList.as_view(), name="search_product"),
    # path('selected/products/', SelectionForOrder.as_view(), name="selected_product"),
    # path('make/order/', MakeOrder.as_view(), name="make_order"),
    # path('export/order/', export_order_list, name='export_order_list'),
    # path('shop/orders/csv/', ExportOrderCSV.as_view(), name="orders_in_csv"),

    # path('sales/', SalesListView.as_view(), name="sales"),
    # path('export-view/', export_view, name='export_view'),

    # path('fproduct/list/<int:cat_id>/',
    #     FeaturedProductList.as_view(), name="featured_products"),

    # path('category/<int:cat_id>/', ClientCategorizedProductList.as_view(),
    #     name='clientcategorizedproductlist'),

    # path('product/<int:pk>/detail/', ProductDetailView.as_view(), name="product_detail"),
    # path('quickview/<int:pk>/', QuickView.as_view(), name="quickview"),

    # path('wish-list/', UsersAllWishList.as_view(), name="users_wish_list"),
    # path('addto/wish-list/<int:prod_id>/', AddToWishList.as_view(), name="to-wish_list"),
    # path('delete/wish-list/<int:pk>/', DeleteWishList.as_view(), name='delete_wish'),
    # path('wish-list/<int:pk>/detail/', WishListProductDetail.as_view(), name="wish_list_detail"),
    # path('get/products-in-wishlist/', GetProductsInWishList.as_view(), name="prod_in_wish_list"),

    # path('addto/cart/<int:prod_id>/', AddToCart.as_view(), name="in-cart"),
    # path('get/products-in-cart/', GetProductsInCart.as_view(), name="prod_in_cart"),
    # path('notify-me/<int:prod_id>/', NotifyMeView.as_view(), name="notify_me"),
    # path('shop/notify-me-list/', NotifyMeList.as_view(), name="notify_me_list"),
    # path('shop/notify-me/<int:pk>/update/', NotifyMeUpdateStatus.as_view(), name='notify_me_update'),
    # path('notify-me/<int:pk>/detail/', NotifyMeDetail.as_view(), name="notify_me_detail"),
    # path('shop/notify-me/<int:pk>/delete/', NotifyMeDelete.as_view(), name='notify_me_delete'),
    # path('shop/multiple/notify-me/delete/', MultipleNotifyMeDeletion.as_view(), name='notify_me_delete_multiple'),

    # path('checkout/', Checkout.as_view(), name='checkout'),
    # path('update/user/detail/<int:user_id>/', CheckoutUserUpdate.as_view(), name='user_detail_update'),
    # # path('apply-coupon/', ApplyCoupon.as_view(), name='apply_coupon'),

    # path('checkout/<int:prod_id>/', CheckoutDirectly.as_view(), name='checkout_directly'),
    # path('confirm/order/', ConfirmOrder.as_view(), name='payment'),
    # path('confirm/order/<int:coupon_id>/', ConfirmOrderWithCoupon.as_view(),
    #     name='confirm-order-with-coupon'),
    # # path('purchase/now/', PurchaseNow.as_view(), name='purchase-now'),
    # path('confirmation/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/(?P<order>\d+)/',
    #     confirmation, name="confirmation"),

    # path('product/<int:prod_id>/remove/', RemoveFromCart.as_view(), name="remove_from_cart"),
    # path('cart-list/', CartList.as_view(), name="all_cart_list"),

    # path('your-orders/<int:pk>/detail', MyOrderDetail.as_view(), name='my_order_detail'),
    # path('your-orders/', MyAllOrders.as_view(), name='my_orders'),
    # path('order/<int:pk>', ClientOrderDetail.as_view(), name='client_order_detail'),
    # path('cancel/order/<int:pk>', CancelOrder.as_view(), name='cancel_order'),

    # path('coupons/', MyCoupons.as_view(), name='my_coupons'),
    # path('coupon/<int:pk>', ClientCouponDetail.as_view(), name='client_coupon_detail'),

    # path('get/product-rate/<int:prod_id>/', GetProductRate.as_view(), name="product_rate"),
    # path('create-rate/<int:prod_id>/', CreateRating.as_view(), name="create_rate"),

    # path('tags/<str:slug>/', TagsProductListView.as_view(), name="tag_products"),


    # # static pages
    # path('new-products/', NewProductList.as_view(), name="new_products"),
    # path('special-products/', SpecialProductList.as_view(), name="special_products"),
    # path('coming-products/', ComingProductList.as_view(), name="upcoming_products"),
    # path('delivery/', DeliveryView.as_view(), name="delivery"),
    # path('terms/', TermsAndConditionsView.as_view(), name="terms_n_conditions"),
    # path('bout/', AboutusView.as_view(), name='about'),
    # path('urstores/', OurStoresView.as_view(), name='ourstores'),

    # # compare
    # path('addto/compare-list/<int:prod_id>/', AddToCompare.as_view(), name="to_compare_list"),
    # path('compare-products/', GetComparingProducts.as_view(), name="compare_products"),
    # path('get/compare-list/<int:prod_id>/', GetComparing.as_view(), name="compare_list"),
    # path('get/products-in-compare/', GetProductsInCompare.as_view(), name="prod_in_compare"),
    # path('remove/from-compare-list/<int:prod_id>/', RemoveFromCompare.as_view(), name="remove_from_compare"),

    # path('update/quantity/<int:prod_id>/', UpdateQuantity.as_view(), name='update_quantity'),

    # path('shop/status/create/', StatusCreateView.as_view(), name="status_create"),
    # path('shop/status/<int:pk>/update/', StatusUpdateView.as_view(), name="status_update"),
    # path('shop/status/', StatusListView.as_view(), name="status"),
    # path('shop/status/<int:pk>/delete/', StatusDeleteView.as_view(), name="status_delete"),
    # path('shop/multiple/status/delete/', MultipleStatusDeletion.as_view(), name='status_delete_multiple'),

    # path('shop/tracker/<int:pk>/update/', TrackerUpdateView.as_view(), name="tracker_update"),
    # path('shop/tracker/list/', TrackerListView.as_view(), name="trackers"),
    # path('track-order/', TrackOrder.as_view(), name="track"),
    # path('tracking-result/', TrackingResult.as_view(), name="tracking_result"),
    # path('tracking-result/<int:tracker_id>/', TrackingResult.as_view(), name="tracking_result"),
    # path('tracking-result-processing/', TrackingResultProcessing.as_view(), name="tracking_result_processing"),

    # path('shop/reviews/', ReviewListView.as_view(), name="reviews"),
    # path('shop/multiple/reviews/delete/', MultipleReviewsDeletion.as_view(), name='reviews_delete_multiple'),
    # path('shop/approve/review/<int:pk>/', ApproveReview.as_view(), name="approve_review"),
    # path('notifications/', NotificationList.as_view(), name="notifications"),
    # path('notifications/mark-as-read/<int:pk>/',
    #     MarkAsRead.as_view(), name='mark_as_read'),
    # path('notifications/mark-all-as-read/',
    #     MarkAllRead.as_view(), name='mark_all_as_read'),
    # # Advertisement
    # path('dvertisement/create/',AdvertisementCreateView.as_view(),
    #     name='advertisement_create'),
    # path('dvertisement/list/',AdvertisementListView.as_view(),
    #     name='advertisement_list'),
    # path('tem/<int:pk>/delete/',
    #     AdvertisementDelete.as_view(), name='advertisement_delete'),
    # path('dvertisement/<int:pk>/update/',
    #     AdvertisementUpdateView.as_view(), name='advertisement_update'),
    # path('multiple/advertisement/delete/', MultipleAdvertisementDeletion.as_view(), name='advertisement_delete_multiple'),


    # path('test/', TestView.as_view(), name='test'),
    # path('check-coupon/', CheckCoupon.as_view(), name='check-coupon'),

    # path('send/notifications/<int:pk>/', NotificationsSend.as_view(), name="notifications_send"),

    # path('get-product-detail/', ProductDetails.as_view(), name='get_product_details'),
    # path('tags/', TagsView.as_view(create_field='title'), name='tags_autocomplete'),
    # path('order/filter/', OrdersFilterView.as_view(), name='order_filter'),
    # path('sales/filter/', SalesFilterView.as_view(), name='sales_filter'),


    # ###############################################################
    # path('shop/', ShopView.as_view(), name='shop'),
    # path('our-story/', OurStoryView.as_view(), name='our_story'),
    # path('sustainability/', SustainabilityView.as_view(), name='sustainability'),

]
