import datetime
import json
import random
import string
from rest_framework.authtoken.models import Token

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from notifications.models import Notification
from notifications.signals import notify
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import UpdateAPIView,CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT
from rest_framework.views import APIView

from account.tokens import account_activation_token
from cart.models import (Cart, Category, FeaturedProduct, Order, Product,
                         ProductInTransaction, Rating, Tracker, Wishlist)
from shop_api.serializers import *
from shop_api.serializers import UserRegistrationSerializer


class UserLoginAPIView(APIView):
    permissions_classes = [AllowAny]
    authentication_classes = (TokenAuthentication,)
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        
        if serializer.is_valid():
            new_data = serializer.data
            user = authenticate(email=new_data['email'], password=new_data['password'])
            if user is not None:
                if user.is_active:
                    login(request, user)
            else:
                return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)
            return Response(new_data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class UserRegisterAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        admin_user = User.objects.filter(is_superuser=True).first()

        if serializer.is_valid():
            new_data = serializer.data
            user = User.objects.create(
                email=new_data['email'], username=new_data['username'],
                contact_no1=new_data['mobile_number'])
            user.set_password(new_data['password'])
            user.is_active = False
            user.save()
            grp = Group.objects.get(name='Customer')
            grp.user_set.add(user)

            current_site = get_current_site(request)
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            mail_subject = 'BreadFruit Electronics: Confirm your email address'
            to_email = user.email
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            valid_from = datetime.datetime.today()
            valid_to = datetime.datetime.today() + datetime.timedelta(days=60)
            code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
            coupon = Coupon.objects.create(
                user=user, title='Registered', discount_amount=100, valid_from=valid_from,
                valid_to=valid_to, code=code)
            notify.send(
                admin_user, recipient=user, verb='Welcome to the breadfruit', action_object=coupon,
                description='coupon')
            return Response(new_data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class UserUpdateAPIView(APIView):
    serializer_class = UserUpdateSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(data=request.data)
        if serializer.is_valid():
            new_data = serializer.data
            user = self.request.user
            user.first_name = serializer.data.get("first_name")
            user.last_name = serializer.data.get("last_name")
            user.gender = serializer.data.get("gender")
            user.birthdate = serializer.data.get("birthdate")
            user.address_line1 = serializer.data.get("address_line1")
            user.address_line2 = serializer.data.get("address_line2")
            user.contact_no1 = serializer.data.get("contact_no1")
            user.contact_no2 = serializer.data.get("contact_no2")
            user.landmark = serializer.data.get("landmark")
            user.city = serializer.data.get("city")
            user.billing_addr = serializer.data.get("billing_addr")
            user.shipping_addr = serializer.data.get("shipping_addr")
            user.save()
            return Response(new_data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors,status=HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class UserUpdateBillingAddressAPIView(APIView):
    serializer_class = UpdateAddressSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = UpdateAddressSerializer(data=request.data)
        if serializer.is_valid():
            new_data = serializer.data
            user = self.request.user
            user.address_line1 = serializer.data.get("address_line1")
            user.contact_no1 = serializer.data.get("contact_no1")
            user.save()
            return Response(new_data, status=HTTP_200_OK)
        else:
            return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)



#Mixin for Product List
class ProductMixin(object):
    def get_product_list(self, query, *args, **kwargs):
        toRet = []
        for prod in query: 
            ratings = Rating.objects.filter(product__id=prod.id)
            toAddTemp = {}
            try:
                wish_prod = Wishlist.objects.get(products__products_id=prod.id, deleted_at=None, user=self.request.user)
                toAddTemp["is_wish"] = True
            except Wishlist.DoesNotExist:
                toAddTemp["is_wish"] = False
            toAddTemp["reviews"] = []
            if ratings.exists():
                total_rating = 0
                count = ratings.count()
                for rate in ratings:
                    total_rating += rate.rate
                    toAddTemp["reviews"].append({'username': rate.user.username, 'review': rate.review ,'rating':rate.rate })
                rating_avg = total_rating / count
                rate = rating_avg
            else:
                rate = 0

            toAddTemp["stock_quantity"] = prod.quantity
            if prod.productintransaction_set.filter(user=self.request.user, deleted_at__isnull=True).count() > 0:
                toAddTemp['cart_quantity'] = str(prod.productintransaction_set.filter(user=self.request.user, deleted_at__isnull=True).first().quantity)
            else:
                toAddTemp['cart_quantity'] = str(1)
            toAddTemp["reviews_count"] = str(len(toAddTemp["reviews"]))+' reviews'
            toAddTemp["rating"] = rate
            # toAddTemp["id"] = prod.id
            toAddTemp["prod_id"] = prod.id
            toAddTemp["name"] = prod.name
            toAddTemp["photos"] = []
            if prod.photos.all():
                for photo in prod.photos.all():
                    phots = 'http://breadfruit.me' + photo.photo.url
                    toAddTemp["photos"].append(phots)
            else:
                toAddTemp["photos"].append('http://breadfruit.me/static/frontend/image/breadfruit-psd.png')
            toAddTemp["tags"] = [tag.title for tag in prod.tags.all()]
            toAddTemp["categories"] = [{
                'id': category.id, 'title': category.title} for category in prod.categories.all()]
            toAddTemp["description"] = prod.description
            toAddTemp["summary"] = prod.summary
            toAddTemp["old_price"] = str(int(prod.old_price))
            toAddTemp["visibility"] = prod.visibility
            if prod.quantity > 0:
                toAddTemp["status"] = 'In Stock'
            else:
                toAddTemp["status"] = 'Out of Stock'
            toAddTemp["quantity"] = str(prod.quantity)
            toAddTemp["reference_code"] = prod.reference_code
            toAddTemp["price"] = int(round(prod.price))
            toAddTemp["is_on_sale"] = prod.is_on_sale
            toAddTemp["vat"] = prod.vat
            toAddTemp["vat_included"] = prod.vat_included
            toAddTemp["vat_amount"] = prod.vat_amount
            toAddTemp["display_old_price"] = str(prod.display_old_price)
            toAddTemp["display_new_price"] = str(prod.display_new_price)
            toAddTemp["discount_percent"] = int(prod.discount_percent)
            toAddTemp["discount_amount"] = prod.discount_amount
            toAddTemp["grand_total"] = int(round(prod.grand_total))
            toAddTemp["you_save"] = str(int(prod.old_price-prod.price))
            toAddTemp["share"] = 'http:breadfruit.me/product/'+str(prod.id)+'/detail/'
            if prod.quantity <= 0:
                toAddTemp["available"] = False
            else:
                toAddTemp["available"] = True
            toRet.append(toAddTemp)
        return HttpResponse(json.dumps(toRet))



class CountCartItemAPI(ProductMixin,APIView):
    """ item get counted each time user added products to cart """
    permission_classes = (IsAuthenticated,)
    
    
    def get(self, request, *args, **kwargs):
        # count = 0
    
        count = Cart.objects.filter(user=self.request.user, deleted_at=None, products__is_ordered=False).count()
        
        # for obj in Cart.objects.filter(user= self.request.user,deleted_at=None):
        #     count += obj.products.quantity
        return JsonResponse({'cart_count': count},status=200)





class ProductListWalnut(ProductMixin, APIView):
    permissions_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        queryset = Product.objects.filter(deleted_at=None)
        qs = self.get_product_list(queryset)
        return Response({'data': qs},status=HTTP_200_OK)

class ProductList(ProductMixin, APIView):
    permissions_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        queryset = Product.objects.filter(deleted_at=None)
        qs = self.get_product_list(queryset)
        return qs 

class SimilarProductList(ProductMixin, APIView):
    permissions_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        product = get_object_or_404(Product, id=kwargs['prod_id'])
        category = product.categories.all()
        queryset = Product.objects.filter(
            categories__in=category, deleted_at__isnull=True).exclude(id=product.id)[:4]
        qs = self.get_product_list(queryset)
        return qs


class SortedProductList(ProductMixin, APIView):
    permissions_classes = [AllowAny]

    def dispatch(self, *args, **kwargs):
        self.cat_id = self.kwargs['cat_id']
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        sort_by = self.request.GET.get('sort_by', None)
        if 'sort_by' in self.request.GET:
            sort_by = self.request.GET['sort_by']
            if sort_by == "1":
                queryset = Product.objects.filter(
                    deleted_at__isnull=True, categories=self.cat_id).order_by('name')
            elif sort_by == "2":
                queryset = Product.objects.filter(
                    deleted_at__isnull=True, categories=self.cat_id).order_by('-name')
            elif sort_by == "3":
                queryset = Product.objects.filter(
                    deleted_at__isnull=True, categories=self.cat_id).order_by('price')
            elif sort_by == "4":
                queryset = Product.objects.filter(
                    deleted_at__isnull=True, categories=self.cat_id).order_by('-price')
            elif sort_by == "5":
                queryset = Product.objects.filter(
                    deleted_at__isnull=True, categories=self.cat_id).order_by('-order_count')
            elif sort_by == "0":
                queryset = Product.objects.filter(
                    deleted_at__isnull=True,
                    categories=self.cat_id)
        else:
            queryset = Product.objects.filter(
                deleted_at__isnull=True, categories=self.cat_id)
        qs = self.get_product_list(queryset)
        return qs


#Product Detail Mixin
class ProductDetailMixin(object):

    def get_product_detail(self,query,*args,**kwargs):

        product = Product.objects.get(id=query)
        ratings = Rating.objects.filter(product__id=product.id)
        toRet = {}

        # toRet["id"] = product.id
        toRet["prod_id"] = product.id
        toRet["photos"] = ['http://breadfruit.me'+str(photo.photo.url) for photo in product.photos.all()]
        toRet["description"] = product.description
        toRet["visibility"] = product.visibility
        toRet["reference_code"] = product.reference_code
        # toRet["quantity"] = product.quantity
        toRet["stock_quantity"] = product.quantity
        if product.productintransaction_set.filter(user=self.request.user, deleted_at__isnull=True).count() > 0:
            toRet['cart_quantity'] = str(product.productintransaction_set.filter(user=self.request.user, deleted_at__isnull=True).first().quantity)
        else:
            toRet['cart_quantity'] = str(1)
        toRet["old_price"] = str(int(product.old_price))
        toRet["price"] = str(int(product.price))
        toRet["vat"] = product.vat
        toRet["vat_included"] = product.vat_included
        toRet["vat_amount"] = product.vat_amount
        toRet["summary"] = product.summary
        toRet["discount_percent"] = int(product.discount_percent)
        toRet["discount_amount"] = product.discount_amount
        toRet["display_new_price"] = product.display_new_price
        toRet["display_old_price"] = product.display_old_price
        toRet["grand_total"] = str(int(product.grand_total))
        toRet["is_new"] = str(product.expire_on)
        toRet["is_on_sale"] = product.is_on_sale
        toRet["you_save"] = product.grand_total-product.old_price
        toRet["is_coming_soon"] = []
        try:
            wish_prod = Wishlist.objects.get(products__products_id=product.id, deleted_at=None, user=self.request.user)
            toRet["is_wish"] = True
        except Wishlist.DoesNotExist:
            toRet["is_wish"] = False
        toRet["categories"] = [{
            'id': category.id, 'title': category.title} for category in product.categories.all()]
        toRet["tags"] = [{
            'id': tag.id, 'title': tag.title} for tag in product.tags.all()]
        toRet["reviews"] = []
        total_rating = 0
        if ratings.exists():
            count = ratings.count()
            for rate in ratings:
                total_rating += rate.rate
                toRet["reviews"].append({'username': rate.user.username, 'review':rate.review})
            rating_avg = total_rating / count
            rate = rating_avg
        else:
            rate = total_rating
        if product.quantity <= 0:
                toRet["available"] = False
        else:
            toRet["available"] = True
        toRet["rating"] = int(rate)
        toRet['status'] = True
        toRet["reviews_count"] = str(len(toRet["reviews"]))+' reviews'
        toRet["share"] = 'http:breadfruit.me/product/'+str(product.id)+'/detail/'
        return JsonResponse(toRet)



class ProductDetail(ProductDetailMixin, APIView):
    permissions_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        product_id = self.kwargs.get('pk')
        product = get_object_or_404(Product, id=product_id)
        if self.request.user.is_authenticated():
            try:
                rview = RecentlyViewed.objects.get(user=self.request.user)
                if rview.products.all().count() > 4:
                    rview.products.remove(rview.products.last())
                rview.products.add(product)
            except RecentlyViewed.DoesNotExist:
                rview = RecentlyViewed.objects.create(user=self.request.user)
                rview.products.add(product)
        product = self.get_product_detail(product_id)
        return product


class UpdateQuantityAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = QuantitySerializer
    model = ProductInTransaction
    queryset = ProductInTransaction.objects.filter(deleted_at__isnull=True)


class SearchByCategoryAPI(generics.ListAPIView):
    serializer_class = ProductSerializer
    model = Product

    def dispatch(self, request, *args, **kwargs):
        cat_id = self.kwargs.get("cat_id")
        try:
            self.category = Category.objects.get(id=cat_id)
        except Category.DoesNotExist:
            raise Http404
        return super(SearchByCategoryAPI, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = Product.objects.filter(
            deleted_at__isnull=True).filter(categories=self.category)
        return qs


class SearchByValueAPI(ProductMixin, APIView):

    def get(self, request, *args, **kwargs):
        queried = self.request.GET.get('q')
        if 'q' in self.request.GET:
            search_product_list = Product.objects.filter(deleted_at__isnull=True).filter(
                Q(name__icontains=queried) | Q(description__icontains=queried))
            items = self.get_product_list(search_product_list)
            return items
        else:
            products = Product.objects.filter(deleted_at__isnull=True)
            return self.get_product_list(products)
            

class CategoryList(View):
    def get(self, request, *args, **kwargs):
        queryset = Category.objects.filter(deleted_at=None).exclude(title="root")
        toRet = []

        for cats in queryset:
            product = Product.objects.filter(categories=cats,deleted_at__isnull=True).first()
            toAddTemp = {}
            toAddTemp["title"] = cats.title
            toAddTemp["id"] = cats.id
            if product:
                if product.photos.all():
                    toAddTemp["photos"] = 'http://breadfruit.me' + product.photos.all().first().photo.url
                else:
                    toAddTemp["photos"] = 'http://breadfruit.me/static/frontend/image/breadfruit-psd.png'      
                toRet.append(toAddTemp)
        return HttpResponse(json.dumps(toRet))


# class SliderList(generics.ListAPIView):
#     serializer_class = e lizer

#     def get_queryset(self):
#         qs = Slider.objects.filter(deleted_at__isnull=True)
#         return qs

class SliderList(APIView):

    def get_product(self, product, user):
        toRet = {}
        ratings = Rating.objects.filter(product__id=product.id)
        toRet['prod_id'] = product.pk
        toRet['name'] = product.name
        toRet['photos'] = ['http://breadfruit.me' + photo.photo.url for photo in product.photos.all()]
        toRet['description'] = product.description
        toRet['categories'] = [{'title': category.title} for category in product.categories.all()]
        toRet['tags'] = [{'title': tag.title} for tag in product.tags.all()]
        toRet['old_price'] = product.old_price
        toRet['visibility'] = product.visibility
        toRet['status'] = 'In Stock' if product.quantity > 0 else 'Out of Stock'
        toRet['quantity'] = product.quantity
        toRet['stock_quantity'] = product.quantity
        toRet['reference_code'] = product.reference_code
        toRet['price'] = product.price
        toRet['is_on_sale'] = product.is_on_sale
        toRet['grand_total'] = product.grand_total
        toRet['vat'] = product.vat
        toRet['vat_included'] = product.vat_included
        toRet['vat_amount'] = product.vat_amount
        toRet["display_old_price"] = product.display_old_price
        toRet["display_new_price"] = product.display_new_price
        toRet['discount_percent'] = int(product.discount_percent)
        toRet['you_save'] = str(product.grand_total-product.old_price)
        toRet['share'] = 'http:breadfruit.me/product/'+str(product.id)+'/detail/'
        toRet['reviews'] = []
        if ratings.exists():
            total_rating = 0
            count = ratings.count()
            for rate in ratings:
                total_rating += rate.rate
                toRet["reviews"].append({'username': rate.user.username, 'review': rate.review ,'rating':rate.rate })
            rating_avg = total_rating / count
            rate = rating_avg
        else:
            rate = 0
        toRet['reviews_count'] = str(len(toRet["reviews"]))+' reviews'
        toRet['rating'] = rate
        toRet['available'] = True if product.quantity > 0 else False
        if user.is_authenticated():
            try:
                Wishlist.objects.get(products__products_id=product.id, deleted_at=None, user=user)
                toRet["is_wish"] = True
            except Wishlist.DoesNotExist:
                toRet["is_wish"] = False
        else:
            toRet['is_wish'] = False
        toRet['summary'] = product.summary
        if user.is_authenticated() :
            if product.productintransaction_set.filter(deleted_at__isnull=True, user=user).count() > 0:
                toRet['cart_quantity'] = str(product.productintransaction_set.filter(deleted_at__isnull=True, user= user).first().quantity)
            else:
                toRet['cart_quantity'] = str(1)
        
        return toRet


    def get(self, request, *args , **kwargs):
        sliders = Slider.objects.filter(deleted_at__isnull=True)
        toRet = []
        for slider in sliders:
            toAdd = {}
            toAdd['id'] = slider.pk
            toAdd['photos'] = 'http://breadfruit.me' + slider.photos.url
            toAdd['url'] = slider.url
            if slider.product:
                toAdd['product'] = self.get_product(slider.product, request.user)
            else:
                toAdd['product'] = None
            if slider.category !=None:
                toAdd['category_id'] = slider.category.id
            else:
                toAdd['category_id'] = -1

            if slider.slider_type != None:
                toAdd['slider_type'] = slider.slider_type
            else:
                toAdd['slider_type'] = 'Slider Type Not Found!!'
            toRet.append(toAdd)
        return HttpResponse(json.dumps(toRet))

class ProductByCategoryAPI(ProductMixin, APIView):
    def get(self, request, *args, **kwargs):
        cat_id = self.kwargs.get("cat_id")
        try:
            category = Category.objects.get(id=cat_id)
        except Category.DoesNotExist:
            raise Http404
        queryset = Product.objects.filter(categories=category, deleted_at__isnull=True)
        return self.get_product_list(queryset)


class CartWishlistMixin(object):

    def get_products(self, query, *args, **kwargs):
        toRet = []
        for cart in query:
            toAddTemp = {}
            toAddTemp['id'] = cart.id
            ratings = Rating.objects.filter(product__id=cart.products.products.id)
            toAddTemp["reviews"] = []
            if ratings.exists():
                total_rating = 0
                count = ratings.count()
                for rate in ratings:
                    total_rating += rate.rate
                    toAddTemp["reviews"].append({'username': rate.user.username, 'review':rate.review,'rating':rate.rate })
                rating_avg = total_rating / count
                rate = rating_avg
            else:
                rate = 5
            toAddTemp["reviews_count"] = str(len(toAddTemp["reviews"]))+' reviews'
            toAddTemp["rating"] = rate
            toAddTemp["prod_id"] = cart.products.products.id
            toAddTemp["pit_id"] = cart.products.id
            toAddTemp["name"] = cart.products.products.name
            toAddTemp["photos"] = []
            if cart.products.products.photos.all():
                for photo in cart.products.products.photos.all():
                    phots = 'http://breadfruit.me' + photo.photo.url
                    toAddTemp["photos"].append(phots)
            else:
                toAddTemp["photos"].append('http://breadfruit.me/static/frontend/image/breadfruit-psd.png')
            if cart.products:
                toAddTemp['cart_quantity'] = str(cart.products.quantity)
            else:
                toAddTemp['cart_quantity'] = str(1)


            toAddTemp["tags"] = [tag.title for tag in cart.products.products.tags.all()]
            toAddTemp["categories"] = [{
                'id': category.id, 'title': category.title} for category in cart.products.products.categories.all()]
            toAddTemp["description"] = cart.products.products.description
            toAddTemp["summary"] = cart.products.products.summary
            toAddTemp["old_price"] = str(cart.products.products.old_price)
            toAddTemp["visibility"] = cart.products.products.visibility
            if cart.products.products.quantity > 0:
                toAddTemp["status"] = 'In Stock'
            else:
                toAddTemp["status"] = 'Out of Stock'
            toAddTemp["quantity"] = str(cart.products.quantity)
            toAddTemp["stock_quantity"] = str(cart.products.products.quantity)
            toAddTemp["reference_code"] = cart.products.products.reference_code
            toAddTemp["price"] = str(cart.products.products.price)
            toAddTemp["is_on_sale"] = cart.products.products.is_on_sale
            toAddTemp["vat"] = cart.products.products.vat
            toAddTemp["vat_included"] = cart.products.products.vat_included
            toAddTemp["vat_amount"] = cart.products.products.vat_amount
            toAddTemp["discount_percent"] = int(cart.products.products.discount_percent)
            toAddTemp["discount_amount"] = int(cart.products.products.discount_amount)
            toAddTemp["grand_total"] = int(cart.products.products.grand_total)
            toAddTemp["display_old_price"] = cart.products.products.display_old_price
            toAddTemp["display_new_price"] = cart.products.products.display_new_price
            toAddTemp["you_save"] = int(cart.products.products.grand_total-cart.products.products.old_price)
            try:
                wish_prod = Wishlist.objects.get(products__products_id=cart.products.products.id, deleted_at=None, user=self.request.user)
                toAddTemp["is_wish"] = True
            except Wishlist.DoesNotExist:
                toAddTemp["is_wish"] = False
            if cart.products.products.quantity <= 0:
                toAddTemp["available"] = False
            else:
                toAddTemp["available"] = True
            toRet.append(toAddTemp)
        return toRet

class ProductsInWishlist(CartWishlistMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        wishlist = Wishlist.objects.filter(user=self.request.user, deleted_at__isnull=True)
        items = self.get_products(wishlist)
        return JsonResponse({'items': items})


class ProductsInCart(CartWishlistMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        carts = Cart.objects.filter(user=self.request.user, deleted_at=None, products__is_ordered=False)
        items = self.get_products(carts)
        return JsonResponse({'items': items})
            

class LatestProducts(ProductMixin, APIView):
    def get(self, request, *args, **kwargs):
        queryset = Product.objects.filter(is_new=True,deleted_at=None).order_by('-created_at')
        qs = self.get_product_list(queryset)
        return qs


class ComingSoonProducts(ProductMixin, APIView):
    def get(self, request, *args, **kwargs):
        queryset = Product.objects.filter(is_coming_soon=True,deleted_at=None).order_by('-created_at')
        qs = self.get_product_list(queryset)
        return qs


class OnSaleProducts(ProductMixin, APIView):

    def get(self, request, *args, **kwargs):
        queryset = Product.objects.filter(is_on_sale=True,deleted_at=None).order_by('-created_at')
        qs = self.get_product_list(queryset)
        return qs


class FeaturedProducts(ProductMixin, APIView):

    def get(self, request, *args, **kwargs):
        queryset = FeaturedProduct.objects.all().order_by('-created_at')
        product_list = []
        for product in queryset:
            ind_product = product.products
            product_list.append(ind_product)
        prod_list = self.get_product_list(product_list)
        return prod_list


class AddToWishList(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['prod_id'])     
        try:
            obj = Wishlist.objects.get(products__products=product, user=request.user)
            if obj.deleted_at:
                obj.deleted_at = None
                status = True
            else:
                obj.deleted_at = timezone.now()
                status = False
            obj.save()
        except Wishlist.DoesNotExist:
            prod_in_tran = ProductInTransaction.objects.create(products=product)
            Wishlist.objects.create(
                products=prod_in_tran, user=request.user)
            status = True
        return JsonResponse({'is_wish': status, 'is_auth': True})


class AddToCart(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['prod_id'])
        prod_in_tran, created = ProductInTransaction.objects.get_or_create(
            user=request.user, products=product, is_ordered=False, deleted_at__isnull=True)
        try:
            obj = Cart.objects.get(products=prod_in_tran, user=request.user, deleted_at=None)
            status = False
            try:
                wish = Wishlist.objects.get(
                    user=request.user, products__products=product, deleted_at__isnull=False)
                wish.deleted_at = None
                wish.save()
            except Wishlist.DoesNotExist:
                pass
        except Cart.DoesNotExist:
            Cart.objects.create(products=prod_in_tran, user=request.user)
            status = True
            try:
                wish = Wishlist.objects.get(
                    user=request.user, products__products=product, deleted_at__isnull=True)
                wish.deleted_at = timezone.now()
                wish.save()
            except Wishlist.DoesNotExist:
                pass
        return JsonResponse({'is_incart': status}, status=200)


class RemoveFromCart(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        cart = get_object_or_404(Cart, pk=kwargs['cart_id'])       
        cart.delete()
        cart.products.delete()
        return JsonResponse({'out_of_cart': True})


class MyOrders(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, query, *args, **kwargs):
        orders = Order.objects.filter(deleted_at__isnull=True, user=self.request.user)
        order_list = []
        for order in orders:
            orderTmp = {}
            items = []
            orderTmp['id'] = order.id
            for prod in order.products.all():
                toAddTemp = {}
                toAddTemp['prod_id'] = prod.products.id
                toAddTemp["name"] = prod.products.name
                items.append(toAddTemp)
            orderTmp['products'] = items
            orderTmp['ordered_date'] = order.created_at
            orderTmp['shipped_date'] = order.shipped_date
            orderTmp['total'] = order.total
            orderTmp['condition_status'] = order.condition_status
            order_list.append(orderTmp)
        return JsonResponse({'data': order_list})       


class Checkout(CartWishlistMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        carts = Cart.objects.filter(user=self.request.user, deleted_at=None, products__is_ordered=False).exclude(
            products__products__quantity__lte=0)
        items = self.get_products(carts)
        total = 0
        for prod in carts:
            total += prod.products.products.grand_total * prod.products.quantity
        total = total
        if self.request.user.address_line1 and self.request.user.contact_no1:
            applicable = True
            return JsonResponse({'products': items, 'total': total, 'address': self.request.user.address_line1,
                'contact': self.request.user.contact_no1, 'applicable': applicable, 'user_id': self.request.user.id },
                status=200)
        else:
            applicable = False
            return JsonResponse({
                'products': items, 'total': total,'applicable': applicable, 'user_id': self.request.user.id }, status=200)


@method_decorator(csrf_exempt, name='dispatch')
class ConfirmOrder(CartWishlistMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        admin_user = User.objects.filter(is_superuser=True).first()
        ordered_by = self.request.user
        my_cart = Cart.objects.filter(
            user=ordered_by, deleted_at__isnull=True, products__is_ordered=False).exclude(
                products__products__quantity__lte=0)
        if my_cart.exists():
           
            items = self.get_products(my_cart)
            obj = Order.objects.create(user=ordered_by, code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]))
            
            total = 0
            for prod in my_cart:
                total += prod.products.products.grand_total * prod.products.quantity
            total = total
            for prod in my_cart:
                prod.deleted_at = timezone.now()
                prod.save()
                obj.products.add(prod.products.id)
                obj.total += prod.products.quantity * prod.products.products.grand_total
                obj.save()
                prod.products.is_ordered = True
                prod.products.save()
                try:
                    wl_obj = Wishlist.objects.get(
                        user=ordered_by, products=prod.products, deleted_at__isnull=True)
                    wl_obj.delete()
                except Wishlist.DoesNotExist:
                    pass
            
            # obj.code = code
            # obj.save()
            Tracker.objects.create(order=obj)
            notify.send(
                admin_user, recipient=ordered_by, verb='You have ordered something', action_object=obj,
                description='order')
            return JsonResponse({
                'items': items, 'status': 'Order confirmed successfully', 'address': ordered_by.address_line1,
                'contact': ordered_by.contact_no1, 'total': total, })
        else:
            return JsonResponse({'status': 'There is no items'})


class ApplyCoupon(CartWishlistMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        code = self.request.GET.get('code', None)
        try:
            try:
                self.coupon_obj = Coupon.objects.get(
                    code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(),
                    is_used=False, user=self.request.user)
                self.validation = True
            except Coupon.DoesNotExist:
                self.coupon_obj = Coupon.objects.get(
                    code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(), is_used=False)
                self.validation = True
        except Coupon.DoesNotExist:
            self.coupon_obj = None
            self.validation = False

        ordered_by = self.request.user
        self.total = 0
        carts = Cart.objects.filter(
            user=ordered_by, deleted_at__isnull=True, products__is_ordered=False).exclude(
                products__products__quantity__lte=0)
        items = self.get_products(carts)
        for prod in carts:
            self.total += prod.products.quantity * prod.products.products.grand_total
        if self.request.user.address_line1 and self.request.user.contact_no1:
            applicable = True
        else:
            applicable = False
        if self.validation:
            if self.coupon_obj.discount_amount > 0:
                self.grand_total = int(self.total - self.coupon_obj.discount_amount)
            elif self.coupon_obj.discount_percent:
                self.grand_total = int(self.total - ((self.total * self.coupon_obj.discount_percent)/100))
            else:
                self.grand_total = int(self.total)
            return JsonResponse({
                'total': self.total, 'after_total': self.grand_total, 'validation': self.validation,
                'coupon': self.coupon_obj.title, 'coupon_id': self.coupon_obj.id, 'items': items,
                'applicable': applicable })
        else:
            self.grand_total = self.total
            return JsonResponse({
                'total': self.grand_total, 'validation': self.validation, 'items': items,
                'applicable': applicable})
        

@method_decorator(csrf_exempt, name='dispatch')
class ConfirmOrderWithCoupon(CartWishlistMixin, APIView):
    permission_classes = (IsAuthenticated,)

    def dispatch(self, *args, **kwargs):
        self.coupon = Coupon.objects.get(id=self.kwargs['coupon_id'])
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        admin_user = User.objects.filter(is_superuser=True).first()
        ordered_by = self.request.user
        carts = Cart.objects.filter(
            user=ordered_by, deleted_at__isnull=True, products__is_ordered=False).exclude(
                products__products__quantity__lte=0)
        if carts.exists():
            obj = Order.objects.create(user=ordered_by,code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]))
            items = self.get_products(carts)
            for prod in carts:
                obj.products.add(prod.products.id)
                obj.total += prod.products.quantity * prod.products.products.grand_total
                obj.save()
                try:
                    wl_obj = Wishlist.objects.get(
                        user=ordered_by, products=prod.products, deleted_at__isnull=True)
                    wl_obj.delete()
                except Wishlist.DoesNotExist:
                    pass
                prod.products.is_ordered = True
                prod.products.save()
            if self.coupon.discount_amount > 0:
                obj.total = int(obj.total - self.coupon.discount_amount)
            elif self.coupon.discount_percent:
                obj.total = int(obj.total - int(((obj.total * self.coupon.discount_percent)/100)))
            else:
                obj.total = int(obj.total)
            
            # obj.code = code
            # obj.save()
            Tracker.objects.create(order=obj)
            if self.coupon.user:
                self.coupon.is_used = True
            else:
                self.coupon.validity_count -= 1
                if self.coupon.validity_count == 0:
                    self.coupon.is_used = True
            self.coupon.save()
            notify.send(
                admin_user, recipient=ordered_by, verb='You have ordered something', action_object=obj,
                description='order')
            return JsonResponse({
                'items': items, 'status': 'Order confirmed successfully', 'address': ordered_by.address_line1,
                'contact': ordered_by.contact_no1, 'total': obj.total, 'can_order':True})
        else:
            return JsonResponse({'status': 'There is no items'})


class CouponListAPI(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CouponSerializer
    model = Coupon

    def get_queryset(self):
        queryset = Coupon.objects.filter(
            user=self.request.user, valid_from__lte=timezone.now(),
            valid_to__gte=timezone.now(), is_used=False, deleted_at__isnull=True)
        return queryset


class CouponDetailAPI(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CouponSerializer
    model = Coupon
    queryset = Coupon.objects.filter(deleted_at__isnull=True)


class NotifyMeCreateAPI(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = NotifyMeSerializer
    model = NotifyMe

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['prod_id'])
        return super(NotifyMeCreateAPI, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = NotifyMeSerializer(data=request.data)

        if serializer.is_valid():
            new_data = serializer.data
            NotifyMe.objects.create(
                email=new_data['email'], remarks=new_data['remarks'], product=self.product)
            return Response(new_data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class NotificationsListAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        notifications = Notification.objects.filter(
            recipient=self.request.user, unread=True)
        toRet = []

        for obj in notifications:
            toAddTemp = {}
            toAddTemp['verb'] = obj.verb
            toAddTemp['time'] = str((datetime.datetime.strftime(obj.timestamp,'%b %d, %Y')))
            
            if obj.description == 'order':
                try:
                    order = Order.objects.get(id=obj.action_object.id)
                    products = []
                    for prod in order.products.all():
                        products.append(prod.products.name)
                    toAddTemp['order_id'] = order.id
                    toAddTemp['title'] = 'Your order has been placed!'
                    toAddTemp['description'] = 'You have ordered '+ str(products) +' with cost Rs.' + str(order.total)
                    toAddTemp['first_letter'] = 'OP'
                    toAddTemp['type'] = 'Order'

                except:
                    pass               
            elif obj.description == 'coupon':
                try:
                    coupon = Coupon.objects.get(id=obj.action_object.id)
                    toAddTemp['coupon_id'] = coupon.id
                    toAddTemp['coupon_code'] = str(coupon.code)
                    toAddTemp['title'] = 'Offer Coupon'
                    toAddTemp['description'] = 'Your got offered coupon with code '+ str(coupon.code)
                    toAddTemp['first_letter'] = 'OC'
                    toAddTemp['type'] = 'Coupon'
                    toAddTemp['valid_to'] =  str((datetime.datetime.strftime(coupon.valid_to,'%b %d, %Y')))


                except:
                    pass                
            else:
                toAddTemp['title'] = 'Welcome to Breadfruit'
                toAddTemp['description'] = 'Enjoy your shoping online from home'
                toAddTemp['first_letter'] = 'WB'

            # if obj.description == 'order':
            #     toAddTemp['url'] = 'http://breadfruit.me/apis/order/'+ str(obj.action_object.id)+'/detail/'
            # elif obj.description == 'coupon':
            #     toAddTemp['url'] = 'http://breadfruit.me/apis/coupon/'+ str(obj.action_object.id)+'/detail/'
            # else:
            #     toAddTemp['url'] = '#'
            toRet.append(toAddTemp)
        return JsonResponse(toRet, safe=False)


class OrderDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        order = get_object_or_404(Order, id=self.kwargs['order_id'])
        toRet = []

        for obj in order.products.all():
            toAddTemp = {}
            toAddTemp['prod_id'] = obj.products.id
            toAddTemp['name'] = obj.products.name
            toAddTemp['quantity'] = obj.quantity
            if obj.products.photos.all():
                toAddTemp["photos"] = 'http://breadfruit.me' + obj.products.photos.first().photo.url
            else:
                toAddTemp["photos"] = '/static/frontend/image/breadfruit-psd.png'
            toRet.append(toAddTemp)

        return JsonResponse({
            'id': order.id, 'products': toRet, 'total': order.total})


class RatingWiseSortingAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        products = Product.objects.filter(deleted_at__isnull=True)
        toRet = []
        for prod in products:
            ratings = prod.rating_set.all()
            if ratings.exists():
                toAddTemp = {}
                total_rating = 0
                count = ratings.count()
                for rate in ratings:
                    total_rating += rate.rate
                rating_avg = total_rating / count
                rate = rating_avg
                toAddTemp['rate'] = rate
                toAddTemp['prod_id'] = prod.id
                toAddTemp["name"] = prod.name
                if prod.photos.all():
                    toAddTemp["photos"] = 'http://breadfruit.me' + prod.photos.all().first().photo.url
                else:
                    toAddTemp["photos"] = '/static/frontend/image/breadfruit-psd.png'
                toAddTemp["tags"] = [tag.title for tag in prod.tags.all()]
                toAddTemp["categories"] = [{
                    'id': category.id, 'title': category.title} for category in prod.categories.all()]
                toAddTemp["description"] = prod.description
                toAddTemp["old_price"] = str(prod.old_price)
                toAddTemp["visibility"] = prod.visibility
                if prod.quantity > 0:
                    toAddTemp["status"] = 'In Stock'
                else:
                    toAddTemp["status"] = 'Out of Stock'
                toAddTemp["quantity"] = str(prod.quantity)
                toAddTemp["reference_code"] = prod.reference_code
                toAddTemp["price"] = str(prod.price)
                toAddTemp["is_on_sale"] = prod.is_on_sale
                toAddTemp["vat"] = prod.vat
                toAddTemp["vat_included"] = prod.vat_included
                toAddTemp["vat_amount"] = prod.vat_amount
                toAddTemp["discount_percent"] = int(prod.discount_percent)
                toAddTemp["discount_amount"] = prod.discount_amount
                toAddTemp["grand_total"] = str(prod.grand_total)
                toAddTemp["you_save"] = str(prod.grand_total-prod.old_price)
                toRet.append(toAddTemp)
        return JsonResponse(toRet, safe=False)


class ProductFromOrder(ProductMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = Order.objects.filter(user=self.request.user)
        product_list = []
        for order in queryset:
            for product in order.products.all():
                product_list.append(product.products)
        qs = self.get_product_list(set(product_list))
        return qs


class IndividualProductOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['prod_id'])
        return super(IndividualProductOrderView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        queryset = Order.objects.filter(user=self.request.user, products__products=self.product)
        orderTmp = []
        for order in queryset:
            toAddTemp = {}
            toAddTemp['id'] = order.id
            toAddTemp['ordered_date'] = str(timezone.localtime(order.created_at).strftime(
                "%Y-%m-%dT%H:%M"))
            if order.shipped_date:
                toAddTemp['shipped_date'] = str(timezone.localtime(order.shipped_date).strftime(
                "%Y-%m-%dT%H:%M"))
            else:
                toAddTemp['shipped_date'] = ''
            toAddTemp['condition_status'] = order.condition_status
            orderTmp.append(toAddTemp)
        return JsonResponse({'orders': orderTmp, 'prod_id': self.product.id, 'name': self.product.name})


class IndividualProductOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request,*args,**kwargs):
        order = Order.objects.get(pk=kwargs['order_id'],user=self.request.user)
        toAddTemp = {}
        toAddTemp['id'] = order.id
        toAddTemp['ordered_date'] = str(timezone.localtime(order.created_at).strftime(
            "%Y-%m-%dT%H:%M"))
        if order.shipped_date:
            toAddTemp['shipped_date'] = str(timezone.localtime(order.shipped_date).strftime(
            "%Y-%m-%dT%H:%M"))
        else:
            toAddTemp['shipped_date'] = ''
        toAddTemp['condition_status'] = order.condition_status
        return JsonResponse(toAddTemp)



class ReviewCreateAPI(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RatingSerializer
    model = Rating

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['prod_id'])
        return super(ReviewCreateAPI, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = RatingSerializer(data=request.data)

        if serializer.is_valid():
            new_data = serializer.data
            rating, created = Rating.objects.get_or_create(product=self.product,
                user=self.request.user)
            rating.rate = new_data['rate']
            rating.review = new_data['review']
            rating.save()
            return Response(new_data, status=HTTP_200_OK)
        return Response(serializer.errors, status=HTTP_400_BAD_REQUEST)


class BuyNowAPI(ProductDetailMixin, APIView):
    permission_classes = [IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product, id=self.kwargs['prod_id'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        prod_in_tran, created = ProductInTransaction.objects.get_or_create(
            user=request.user, products=self.product, is_ordered=False, deleted_at__isnull=True)
        if not created:
            if not self.request.GET.get('quantity'):
                prod_in_tran.quantity += 1
            else:
                prod_in_tran.quantity = int(self.request.GET.get('quantity'))
        else:
            if not self.request.GET.get('quantity'):
                pass
            else:
                prod_in_tran.quantity = int(self.request.GET.get('quantity'))
        prod_in_tran.save() 
        try:
            obj = Cart.objects.get(products=prod_in_tran, user=request.user, deleted_at=None)
            try:
                wish = Wishlist.objects.get(
                    user=request.user, products__products=self.product, deleted_at__isnull=False)
                wish.deleted_at = None
                wish.save()
            except Wishlist.DoesNotExist:
                pass
        except Cart.DoesNotExist:
            Cart.objects.create(products=prod_in_tran, user=request.user)
            try:
                wish = Wishlist.objects.get(
                    user=request.user, products__products=self.product, deleted_at__isnull=True)
                wish.deleted_at = timezone.now()
                wish.save()
            except Wishlist.DoesNotExist:
                pass

        productObj =  self.get_product_detail(self.product.id)
        return productObj


class ChangePasswordAPIView(UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    queryset = User.objects.filter(is_active=True)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        return Response(status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.data.get("old_password")):
                raise serializers.ValidationError("Wrong old password.") 

            if serializer.data.get("new_password") != serializer.data.get("confirm_password"):
                raise serializers.ValidationError("Password does not match!")
            else:    
                user.set_password(serializer.data.get("new_password"))
                user.save()
                return Response("Success", status=status.HTTP_200_OK)
        else:
            raise serializers.ValidationError("Kuch toh gadbad hai Nisha....")


class UserCurrentAddress(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if self.request.user.address_line2 and self.request.user.contact_no2:
            return JsonResponse({
                'permanent_address': self.request.user.address_line1,
                'contact_number': self.request.user.contact_no1,
                'billing_addr': self.request.user.address_line2,
                'emergency_contact_number': self.request.user.contact_no2,
            })
        else:
            return JsonResponse({
                'permanent_address': self.request.user.address_line1,
                'contact_number': self.request.user.contact_no1,
            })


class SearchWithMultipleCategories(ProductMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        cat_id_array = self.request.GET.getlist('data')
        products = Product.objects.filter(
            deleted_at__isnull=True).filter(categories__id__in=cat_id_array).order_by('name')
        qs = self.get_product_list(products)
        return qs


class RecentlyViewedProducts(ProductMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            rview = RecentlyViewed.objects.get(user=self.request.user)
            products = rview.products.all()
            qs = self.get_product_list(products)
            return qs
        except RecentlyViewed.DoesNotExist:
            toRet = []
            return JsonResponse(toRet, safe=False)

class IncreaseProductInTransaction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request,*args,**kwargs):
        prod = get_object_or_404(Product, pk=kwargs.get('product_id'))
        prod_in_tran, created = ProductInTransaction.objects.get_or_create(user=request.user, products=prod, is_ordered=False, deleted_at__isnull=True)
        if not created:
            prod_in_tran.quantity += int(kwargs.get('quantity'))
        else:
            prod_in_tran.quantity = int(kwargs.get('quantity'))
        prod_in_tran.save()

        return JsonResponse({'quantity':prod_in_tran.quantity}, status=200)
        

class DecreaseProductInTransaction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        product = get_object_or_404(Product, pk=kwargs.get('product_id'))
        
        try:
            prod_in_tran = ProductInTransaction.objects.get(products=product, user=request.user, is_ordered=False, deleted_at__isnull=True)
            prod_in_tran.quantity -= int(kwargs.get('quantity'))
            prod_in_tran.save()
            return JsonResponse({'quantity':prod_in_tran.quantity}, status=200)
        except:
            return JsonResponse({'quantity':0}, status=200)
        # prod_in_tran = get_object_or_404(ProductInTransaction, products=product, user=request.user, is_ordered=False, deleted_at__isnull=True)
        
        
class UpdateProductInTransaction(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        prod = get_object_or_404(Product, pk=kwargs.get('product_id'))
        prod_in_tran, created = ProductInTransaction.objects.get_or_create(user=request.user, products=prod, is_ordered=False, deleted_at__isnull=True)
        
        prod_in_tran.quantity = int(kwargs.get('quantity'))
        prod_in_tran.save()

        return JsonResponse({'cart_quantity':str(prod_in_tran.quantity)}, status=200)
        

class ProductInTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        prod_in_trans = ProductInTransaction.objects.filter(user=request.user).values()

        return JsonResponse(list(prod_in_trans), safe=False)


class StockCheckFromWalnut(CreateAPIView):

    def post(self,request,*args,**kwargs):
        error = False
        error_products = []

        for data in request.data:
            product=Product.objects.get(name=data['name'])
            if product.quantity < data['quantity']:
                error = True
                error_products.append(product.name)      

        if error == True:
            return Response(error_products, status=HTTP_409_CONFLICT)

        for data in request.data:
            product=Product.objects.get(name=data['name'])
            product.quantity = product.quantity - int(data['quantity'])
            product.save()

        return Response(status=HTTP_200_OK)



class StockCheckFromWalnutRefund(CreateAPIView):

    def post(self,request,*args,**kwargs):
        res=[]
        for data in request.data:
            product=Product.objects.filter(name=data['name']).first()
            if product.quantity < data['product_quantity_change']:
                res.append({
                        'refund_id':data.get('refund_id',None),
                        'product_object_id':data.get('product_object_id',None),
                        'refund_quantity':data.get('refund_quantity',None),
                        'success':False,
                    })
            else:
                res.append({
                        'refund_id':data.get('refund_id',None),
                        'product_object_id':data.get('product_object_id',None),
                        'refund_quantity':data.get('refund_quantity',None),
                        'success':True,
                    })
                product.quantity = product.quantity-int(data['product_quantity_change'])
                product.save()                          

        return Response({'res':res},status=HTTP_200_OK)

