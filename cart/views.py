import urllib.request
import json
import random
import string
import datetime
import time
from itertools import chain

from django.utils import timezone
from django.urls import reverse_lazy, reverse, resolve
from django.shortcuts import get_object_or_404, render
from django.views.generic import (
    CreateView, ListView, UpdateView, FormView, View,
    DetailView, TemplateView)
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages

from django.db.models import Q, Max
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from notifications.models import Notification
from notifications.signals import notify

from .models import *
from .forms import *
from account.models import User, CURRENT_DOMAIN, ShippingAddress
# from account.forms import *

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage


""" variable set to up-to-date dollar price through link provided """


# money_rate_api = "https://openexchangerates.org/api/latest.json?app_id=4087e7681597460796e0c7631ea3378b"
# r = urllib.request.urlopen(url=money_rate_api)
# data = json.loads(r.read().decode())
# rates = data["rates"]
# exchange_rate = rates["NPR"]

exchange_rate = ''


class ClientMixin(object):

    def cart_object(self):
        admin_user = User.objects.filter(is_superuser=True).first()
        if self.request.user.is_authenticated:
            try:
                Coupon.objects.get(user=self.request.user, title='Registered')
            except Coupon.DoesNotExist:
                valid_from = datetime.datetime.today()
                valid_to = datetime.datetime.today() + datetime.timedelta(days=60)
                code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
                coupon = Coupon.objects.create(
                    user=self.request.user, title='Registered', discount_amount=100, valid_from=valid_from,
                    valid_to=valid_to, code=code)
                notify.send(
                    admin_user, recipient=self.request.user, verb='Welcome to the breadfruit',
                    action_object=coupon, description='coupon')
            qs = Cart.objects.filter(
                user=self.request.user, deleted_at__isnull=True, products__is_ordered=False)
            my_cart = []
            for obj in qs:
                my_cart.append(obj)
            if 'into_cart' in self.request.session:
                for obj_id in self.request.session['into_cart']:
                    obj = Cart.objects.get(id=obj_id, products__is_ordered=False, deleted_at=None)
                    try:
                        cart = Cart.objects.get(
                            user=self.request.user, products__products__id=obj.products.products.id,
                            deleted_at__isnull=True, products__is_ordered=False)
                        cart.products.quantity += obj.products.quantity
                        cart.products.save()
                        obj.user = self.request.user
                        obj.deleted_at = timezone.now()
                        obj.save()
                        obj.products.user = self.request.user
                        obj.products.deleted_at = timezone.now()
                        obj.products.save()
                    except Cart.DoesNotExist:
                        obj.user = self.request.user
                        obj.products.user = self.request.user
                        obj.products.save()
                        obj.save()
                    my_cart.append(obj)
            if 'into_cart' in self.request.session:
                del self.request.session['into_cart']
            cart_object = my_cart
        else:
            my_cart = []
            if 'into_cart' in self.request.session:
                for obj_id in self.request.session['into_cart']:
                    obj = Cart.objects.get(id=obj_id, products__is_ordered=False, deleted_at=None)
                    my_cart.append(obj)
            cart_object = my_cart
        cart_list = cart_object
        return cart_list
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart_obj = self.cart_object()
        # del self.request.session['into_cart']
        context['title'] = "Home"
        context['home'] = True
        context['products'] = Product.objects.filter(
            deleted_at__isnull=True)
        context['sliders'] = Slider.objects.filter(deleted_at__isnull=True)
        if self.request.user.is_authenticated:
            context['wishlist'] = Wishlist.objects.filter(
                user=self.request.user, deleted_at__isnull=True)
        context['my_cart'] = cart_obj
        context['my_count'] = len(cart_obj)
        cart_count = 0
        for cnt in cart_obj:
            cart_count += cnt.products.quantity
        context['cart_count'] = cart_count
        if self.request.user.is_authenticated:
            context['notifications'] = Notification.objects.filter(
                recipient=self.request.user, unread=True)
            cart_items = Cart.objects.filter(
                user=self.request.user, products__is_ordered=False, deleted_at__isnull=True)
            cart_list = []
            for item in cart_items:
                cart_list.append(item.products.products)
            context['cart_items'] = cart_list
        sub_total = 0
        for obj in cart_obj:
            cart = Cart.objects.get(id=obj.id, products__is_ordered=False, deleted_at=None)
            sub_total += cart.products.quantity * float(cart.products.products.grand_total)
        context['sub_total'] = float(sub_total)
        context['categories'] = Category.objects.filter(deleted_at=None)[:5]
        # if self.request.GET.get('currency') == 'USD':
        #     self.request.session['conversion'] = self.request.GET.get('currency')
        # elif self.request.GET.get('currency') == 'NPR':
        #     self.request.session['conversion'] = self.request.GET.get('currency')
        # elif not 'conversion' in self.request.session or not self.request.session['conversion']:
        #     self.request.session['conversion'] = 'NPR'
        # else:
        #     self.request.session['conversion'] = self.request.session['conversion']
        # context['exchange_rate'] = exchange_rate
        context['tracking_form'] = TrackingForm

        return context

class RobotsTemplateView(TemplateView):
    template_name = 'robots.txt'
    content_type = 'text/plain' 


class CountCartItem(ClientMixin, View):
    """ item get counted each time user added products to cart """
    
    def get(self, request, *args, **kwargs):
        count = 0
        for obj in self.cart_object():
            count += obj.products.quantity
        return JsonResponse({'cart_count': count}, status=200)


class MyCartItem(ClientMixin, View):
    """  """
    
    def get(self, request, *args, **kwargs):
        toAddTemp = []
        sub_total = 0
        for each in self.cart_object():
            toRet = {}
            product = each.products
            toRet['id'] = each.id
            toRet['product'] = product.products.name
            toRet['quantity'] = product.quantity
            toRet['price'] = product.products.price
            toAddTemp.append(toRet)
        for prod in self.cart_object():
            sub_total += prod.products.products.grand_total * prod.products.quantity
        return render(request, template_name='layouts/frontend/my_cart_ajax.html', context={
            'my_cart':toAddTemp, 'sub_total': sub_total})


class CountWishListItem(ClientMixin, View):
    """ item get counted each time user added products to wishlist """

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            count = Wishlist.objects.filter(
                user=self.request.user, deleted_at__isnull=True).count()
            return JsonResponse({'wishlist_count': count}, status=200)
        return JsonResponse({'wishlist_count': 0}, status=200)


class ClientCategorizedProductList(ClientMixin, ListView):
    template_name = 'frontend/shop.html'
    model = Product

    def dispatch(self, *args, **kwargs):
        self.cat_id = self.kwargs['cat_id']
        return super().dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_name'] = Category.objects.get(id=self.cat_id)
        context['title'] = Category.objects.get(id=self.cat_id).title
        context['og_desc'] = Category.objects.get(id=self.cat_id).description
        category = context['category_name']
        context['seo_keywords'] = category.get_seo_keywords 
        return context

    def get_queryset(self, **kwargs):
        sort_by = self.request.GET.get('sort_by', None)
        if 'sort_by' in self.request.GET:
            sort_by = self.request.GET['sort_by']
            if sort_by == "1":
                queryset_list = Product.objects.filter(
                    deleted_at__isnull=True,
                    categories=self.cat_id).order_by('name')
            elif sort_by == "2":
                queryset_list = Product.objects.filter(
                    deleted_at__isnull=True,
                    categories=self.cat_id).order_by('-name')
            elif sort_by == "3":
                queryset_list = Product.objects.filter(
                    deleted_at__isnull=True,
                    categories=self.cat_id).order_by('price')
            elif sort_by == "4":
                queryset_list = Product.objects.filter(
                    deleted_at__isnull=True,
                    categories=self.cat_id).order_by('-price')
            elif sort_by == "0":
                queryset_list = Product.objects.filter(
                    deleted_at__isnull=True,
                    categories=self.cat_id)
        else:
            queryset_list = Product.objects.filter(
                deleted_at__isnull=True,
                categories=self.cat_id)
        paginator = Paginator(queryset_list, 12)

        page = self.request.GET.get('page')
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        return queryset




class SearchResult(ClientMixin, TemplateView):
    template_name = 'layouts/frontend/search_result.html'
   
    def search_by_name(self,  query):
        keywords = query.split()
        
        q = Q(pk__lt=1)
       
        for key in keywords:
            q =q | (Q(name__icontains=key))

        searched_result = Product.objects.filter(q, deleted_at__isnull=True).order_by()
        
        return searched_result

    # def search_by_description(self,  query):
    #     keywords = query.split()
        
    #     q = Q(pk__lt=1)
       
    #     for key in keywords:
    #         q =q | (Q(description__icontains=key))

    #     searched_result = Product.objects.filter(q, deleted_at__isnull=True)
        
    #     return searched_result


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_queried = self.request.GET.get('category_search', None)
        product_queried = self.request.GET.get('product_search', None)
        if 'product_search' in self.request.GET:
            category_queried = self.request.GET['category_search']
            product_queried = self.request.GET['product_search']
            context['category'] = category_queried
            context['title'] = product_queried
            
            if category_queried == "0":

                search_product_list = (self.search_by_name(product_queried)).distinct()                
                paginator = Paginator(search_product_list, 12)

                page = self.request.GET.get('page')
               
                try:
                    query_set = paginator.page(page)
                    
                except PageNotAnInteger:
                 
                    query_set = paginator.page(1)
                except EmptyPage:
                    query_set = paginator.page(paginator.num_pages)
                context['object_list'] = query_set
               
                return context

            else:
                search_product_list = (self.search_by_name(product_queried).filter(categories__title__iexact=category_queried)).distinct()
                paginator = Paginator(search_product_list, 12)

                page = self.request.GET.get('page')
                try:
                    query_set = paginator.page(page)
                except PageNotAnInteger:
                    query_set = paginator.page(1)
                except EmptyPage:
                    query_set = paginator.page(paginator.num_pages)
                context['object_list'] = query_set
                return context


class ProductDetailView(ClientMixin, DetailView):
    template_name = 'frontend/product_detail.html'
    model = Product

    def get_context_data(self, **kwargs):
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['title'] = self.get_object().name
        context['og_img'] = self.get_object().photos.first()
        context['og_desc'] = self.get_object().summary
        context['image'] = self.get_object().photos.first()
        keywords = self.get_object().get_seo_keywords
        context['seo_keywords'] = (','.join(item.title for item in keywords))
        context['seo_description'] = self.get_object().seo_description
        context['form'] = RatingForm
        context['reviews'] = Rating.objects.filter(product=self.get_object().id, is_approved=True)
        review = Rating.objects.filter(product=self.get_object().id, is_approved=True).count()
        context['review_count'] = review if review else 1
        ratings = Rating.objects.filter(product=self.get_object().id)
        if ratings.exists():
            total_rating = 0
            count = ratings.count()
            for rate in ratings:
                total_rating += rate.rate
            rating_avg = total_rating / count
            rate = rating_avg
        else:
            rate = 0
        context['rating_value'] = int(rate) if rate else 5
        best_rating = Rating.objects.filter(product=self.get_object().id).aggregate(Max('rate')).get('rate__max')
        context['bestrating'] = best_rating if best_rating else 0
        photos = self.get_object().photos.filter(deleted_at__isnull=True)
        context['images'] = ('","http://breadfruit.me'.join(item.photo.url for item in photos))
        if self.request.user.is_authenticated:
            try:
                rated = Rating.objects.get(user=self.request.user, product=self.get_object().id)
                context['rated'] = rated
            except Rating.DoesNotExist:
                pass
        context['home'] = False
        context['qtyform'] = QuantityForm
        context['similar_product'] = get_similar_products(self.get_object())
        product = self.get_object().id

        if self.request.user.is_authenticated:
            try:
                prod_in_tran = ProductInTransaction.objects.get(
                    user=self.request.user, products=product, is_ordered=False, deleted_at__isnull=True)
                try:
                    cart = Cart.objects.get(
                        products=prod_in_tran, products__is_ordered=False,  user=self.request.user, deleted_at__isnull=True)
                    status = True
                    context['pit'] = int(cart.products.quantity)
                except Cart.DoesNotExist:
                    status = False
            except ProductInTransaction.DoesNotExist:
                status = False
            try:
                rview = RecentlyViewed.objects.get(user=self.request.user)
                if rview.products.all().count() > 4:
                    rview.products.remove(rview.products.last())
                rview.products.add(self.get_object())
            except RecentlyViewed.DoesNotExist:
                rview = RecentlyViewed.objects.create(user=self.request.user)
                rview.products.add(self.get_object())
        else:
            if not 'into_cart' in self.request.session or not self.request.session['into_cart']:
                status = False
            else:
                cart_list = self.request.session['into_cart']
                try:
                    cart = Cart.objects.get(
                        id__in=cart_list, products__is_ordered=False, deleted_at__isnull=True, products__products__id=product)
                    status = True
                    context['pit'] = int(cart.products.quantity)                       
                except Cart.DoesNotExist:
                    status = False
        if status:
            context['cart'] = cart
        context['status'] = status

        return context


def get_similar_products(product):
    category = product.categories.all()
    products = Product.objects.filter(
        categories__in=category, deleted_at__isnull=True).exclude(id=product.id)
    return products[:4]


class AddToWishList(View):

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            profile = User.objects.get(username=request.user)
            product = get_object_or_404(Product, pk=kwargs['prod_id'])
            prod_in_tran, created = ProductInTransaction.objects.get_or_create(
                user=request.user, products=product, is_ordered=False, deleted_at__isnull=True)       
            try:
                obj = Wishlist.objects.get(
                    products=prod_in_tran, user=profile)
                if obj.deleted_at:
                    obj.deleted_at = None
                    status = True
                else:
                    obj.deleted_at = timezone.now()
                    status = False
                # obj.products.deleted_at = timezone.now()
                # obj.products.save()
                obj.save()
            except Wishlist.DoesNotExist:
                Wishlist.objects.create(
                    products=prod_in_tran, user=profile)
                status = True
            return JsonResponse({'is_wish': status})
        else:
            return JsonResponse({'is_auth': False})


class GetProductsInWishList(View):
    def get(self, request, **kwargs):
        wish_list = []
        if self.request.user.is_authenticated:
            wishlists = Wishlist.objects.filter(
                user=self.request.user, deleted_at__isnull=True)
            for wishes in wishlists:
                wish_list.append(wishes.products.products.id)
        return JsonResponse({'wish_list': wish_list})


class UsersAllWishList(LoginRequiredMixin, ClientMixin, ListView):
    template_name = 'layouts/frontend/wishlist.html'

    def queryset(self):
        queryset = Wishlist.objects.filter(
            user=self.request.user, deleted_at__isnull=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['home'] = False
        return context


class DeleteWishList(LoginRequiredMixin, UpdateView):
    template_name = 'layouts/frontend/remove_wish.html'
    model = Wishlist
    form_class = WishDeleteForm
    success_url = reverse_lazy('cart:users_wish_list')

    def form_valid(self, form):
        form.instance.deleted_at = timezone.now()
        form.save()
        return super().form_valid(form)


class AddToCart(View):

    def post(self, request,*args, **kwargs):
        
        if request.user.is_authenticated:
            product = get_object_or_404(Product, pk=kwargs['prod_id'])
            prod_in_tran, created = ProductInTransaction.objects.get_or_create(
                user=request.user, products=product, is_ordered=False, deleted_at__isnull=True)
            if not created:
                    prod_in_tran.quantity += 1
            else:
                pass
            prod_in_tran.save()
            try:
                obj = Cart.objects.get(products=prod_in_tran, products__is_ordered=False, user=request.user, deleted_at=None)
                try:
                    wish = Wishlist.objects.get(
                        user=request.user, products__products=product, deleted_at__isnull=False)
                    wish.deleted_at = None
                    wish.save()
                except Wishlist.DoesNotExist:
                    pass
            except Cart.DoesNotExist:
                Cart.objects.create(products=prod_in_tran, user=request.user)               
                try:
                    wish = Wishlist.objects.get(
                        user=request.user, products__products=product, deleted_at__isnull=True)
                    wish.deleted_at = timezone.now()
                    wish.save()
                except Wishlist.DoesNotExist:
                    pass
            cart_list = Cart.objects.filter(user=request.user,products__is_ordered=False, deleted_at__isnull=True)
            x = render_to_string('frontend/cart-items.html',
                {'cart_list': cart_list, 'sub_total':sub_total(cart_list)})
            return HttpResponse(x)
        else:
            created = True
            product = get_object_or_404(Product, pk=kwargs['prod_id'])
            if not 'into_cart' in request.session or not request.session['into_cart']:
                print('session')
                prod_in_tran = ProductInTransaction.objects.create(
                    products=product, is_ordered=False, user=None, is_taken=True)
                obj = Cart.objects.create(products=prod_in_tran)
                request.session['into_cart'] = [obj.id]
            else:
                pit_qs = ProductInTransaction.objects.filter(deleted_at__isnull=True, user=None, is_taken=True, products=product)
                cart_qs = Cart.objects.filter(user=None, products__is_ordered=False,  products__in=pit_qs)

                print(cart_qs,"sss")
                print(self.request.session['into_cart'])

                for cart_obj in cart_qs:
                    if cart_obj.id in self.request.session['into_cart']:
                        print(cart_obj.products,"aasdadsa")
                        cart_obj.products.quantity +=1
                        cart_obj.products.save()
                        created = False
                if created:
                    prod_in_tran = ProductInTransaction.objects.create(
                        products=product, is_ordered=False, user=None, is_taken=True)
                    obj = Cart.objects.create(products=prod_in_tran)
                    saved_list = request.session['into_cart']
                    saved_list.append(obj.id)
                    request.session['into_cart'] = saved_list
              
            session_cart = request.session['into_cart']
            cart_list = Cart.objects.filter(id__in=session_cart, products__is_ordered=False, deleted_at__isnull=True).distinct()
            x = render_to_string('frontend/cart-items.html',
                {'cart_list': cart_list, 'sub_total':sub_total(cart_list)})
            return HttpResponse(x)


class NotifyMeView(CreateView):
    template_name = 'cart/notify_me.html'
    model = NotifyMe
    form_class = NotifyMeForm

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['prod_id'])
        return super(NotifyMeView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        
        form.instance.product = self.product
        if self.request.user.is_authenticated:
            form.instance.email = self.request.user.email
            form.instance.is_guest = False
        else:
            obj = form.save(commit = False)
          
            obj.save()
        form.save()
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

    def form_invalid(self,form):
        if self.request.is_ajax():
            return JsonResponse({'errors':form.errors})
        else:
            return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super(NotifyMeView, self).get_context_data(**kwargs)
        context['object'] = self.product
        return context


def sub_total(carts):
    print(carts,"sub")
    sub_total = 0
    for cart in carts:
        sub_total += cart.products.quantity * float(cart.products.products.grand_total)
    return float(sub_total)

class GetProductsInCart(View):
    def get(self, request, **kwargs):
        if request.user.is_authenticated:
            cart_list = Cart.objects.filter(user=request.user, products__is_ordered=False, deleted_at__isnull=True)   
        else:
            if request.session['into_cart']:
                session_cart = request.session['into_cart']
                cart_list = Cart.objects.filter(id__in=session_cart, products__is_ordered=False, deleted_at__isnull=True)
        x = render_to_string('frontend/cart-items.html', {'cart_list': cart_list, 'sub_total':sub_total(cart_list)})
        return HttpResponse(x)


class RemoveFromCart(View):

    def get(self, request, **kwargs):
        cart = get_object_or_404(Cart, pk=kwargs['prod_id'])
        if cart.user:
            cart.deleted_at = timezone.now()
            cart.save()
        else:
            list_cart = request.session['into_cart']
            list_cart.remove(cart.id)
            request.session['into_cart'] = list_cart
        cart.delete()
        cart.products.delete()
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


class CheckCoupon(View):
    def get(self, request, *args, **kwargs):
        code = self.request.GET.get('code', None)
        if not code == None:
            code = code.lower()
        try:
            try:
                self.coupon_obj = Coupon.objects.get(
                    code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(),
                    is_used=False, user=self.request.user)
            except Coupon.DoesNotExist:
                self.coupon_obj = Coupon.objects.get(
                    code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(), is_used=False)
            self.validation = True
            
        except Coupon.DoesNotExist:
            self.validation = False     

        if self.validation:
             return JsonResponse({'status':True, 'coupon':self.coupon_obj.code }, status=200)
        return JsonResponse({'message':"InValid Code", 'status':False}, status=200)


# class Checkout(ClientMixin, ListView):
#     template_name = 'frontend/checkout.html'
#     validation = False

#     def dispatch(self, request, **kwargs):
#         code = self.request.GET.get('code', None)
#         if self.request.user.is_authenticated or request.user.is_superuser:
#             if not code == None:
#                 code = code.lower()
#             try:
#                 try:
#                     self.coupon_obj = Coupon.objects.get(
#                         code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(),
#                         is_used=False, user=self.request.user)
#                 except Coupon.DoesNotExist:
#                     self.coupon_obj = Coupon.objects.get(
#                         code=code, valid_from__lte=timezone.now(), valid_to__gte=timezone.now(), is_used=False)
#                 self.validation = True
#             except Coupon.DoesNotExist:
#                 self.validation = False

#             ordered_by = self.request.user
#             self.total = 0
#             my_cart = Cart.objects.filter(
#                 user=ordered_by, deleted_at__isnull=True, products__is_ordered=False).exclude(
#                     products__products__quantity__lte=0)
#             queryset = my_cart
#             for prod in queryset:
#                 self.total += prod.products.quantity * prod.products.products.grand_total
#             if self.request.user.street_name and self.request.user.contact_no1:
#                 self.applicable = True
#             else:
#                 self.applicable = False
#             if  self.validation:
#                 if self.coupon_obj.discount_amount > 0:
#                     self.grand_total = self.total - self.coupon_obj.discount_amount
#                 elif self.coupon_obj.discount_percent:
#                     self.grand_total = self.total - ((self.total * self.coupon_obj.discount_percent)/100)
#                 else:
#                     self.grand_total = self.total
#             else:
#                 self.grand_total = self.total
#         return super().dispatch(request, **kwargs)

#     def get_queryset(self, *args, **kwargs):
#         queryset = []
#         if self.request.user.is_authenticated:
#             my_cart = Cart.objects.filter(
#                 user=self.request.user, deleted_at__isnull=True, products__is_ordered=False).exclude(
#                 products__products__quantity__lte=0)
#             queryset = my_cart
#         else:
#             if 'into_cart' in self.request.session:
#                 return Cart.objects.filter(pk__in=self.request.session['into_cart'])
#             # my_cart = []
#             # cart_ids = []
#             # if 'into_cart' in self.request.session:
#             #     for obj_id in self.request.session['into_cart']:
#             #         cart_ids.append(obj_id)
#             #         obj = Cart.objects.get(id=obj_id)
#             #         my_cart.append(obj)
#             # queryset = my_cart 
#         return queryset

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['payment'] = PaymentForm()
#         if self.request.user.is_authenticated:
#             data = User.objects.get(id = self.request.user.pk)
#             context['data'] = data
#             context['form'] = UserForm(initial=data.__dict__)
#         else:
#             context['form'] = GuestForm()
#         context['home'] = False
#         if self.request.user.is_authenticated:
#             context['cform'] = CouponApplyForm
#             context['coupons'] = Coupon.objects.filter(user=self.request.user)
#             context['total'] = self.total
#             context['home'] = False
#             context['validation'] = self.validation
#             context['applicable'] = self.applicable
#             context['grand_total'] = self.grand_total
#             context['payment'] = PaymentForm()

#             if self.validation:
#                 context['coupon'] = self.coupon_obj
#             if self.request.user.street_name and self.request.user.contact_no1:
#                 context['applicable'] = True
#             else:
#                 context['applicable'] = False      
#         return context

class CheckoutUserUpdate(ClientMixin, UpdateView):
    template_name = 'frontend/checkout.html'
    model = User
    form_class = UserForm
    success_url = reverse_lazy("cart:payment")

    def get_object(self):
        user = User.objects.get(pk=self.kwargs['user_id'])
        return user


    def form_valid(self, form):
        user = self.get_object()
        my_cart = Cart.objects.filter(
                user=user, deleted_at__isnull=True, products__is_ordered=False)
                # .exclude(
                # products__products__quantity__lte=0)
        queryset = my_cart
        code= ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
        order = Order.objects.create(user=user, code= code)

        admin_user = User.objects.filter(is_superuser=True).first()
        notify.send(
                    order, recipient=admin_user, verb='A new order has been placed.',
                    action_object=order, description='order')

        for prod in queryset:
            order.products.add(prod.products.id)
            order.total += prod.products.quantity * prod.products.products.grand_total
            order.save()
            prod.products.is_ordered = True
            prod.products.save()
        Tracker.objects.create(order=order)
        if 'into_cart' in self.request.session:
            del self.request.session['into_cart']   
        self.request.session['user'] = user.id
        # current_site = get_current_site(self.request)
        # message = render_to_string('confirmation_for_order.html', {
        #     'user': user, 
        #     'domain': current_site.domain,
        #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        #     'token': account_activation_token.make_token(user),
        #     'oid': order.id,
        #     'order': order,
        #     'tracking_code': order.code
        # })
        # mail_subject = 'BreadFruit Electronics: Orders confirmed'
        # to_email = user.email
        # email = EmailMessage(mail_subject, message, to=[to_email])
        # email.send()
        user.save()
        # messages.success(self.request, "Order Placed Successfully. Check your email for further information")
        return super().form_valid(form)

        # my_cart = []
        # if 'into_cart' in self.request.session:
        #     for obj_id in self.request.session['into_cart']:
        #         obj = Cart.objects.get(id=obj_id)
        #         obj.user = user
        #         obj.products.user = user
        #         obj.save()
        #         my_cart.append(obj)
        # queryset = my_cart
        # code= ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
        # order = Order.objects.create(user=user, code= code)
        # staffs = Staff.objects.filter(deleted_at=None)
        # subject = 'New order'
        # mail_message = 'New Order has been placed. Please Review' 
        # for staff in staffs:
        #     to_email = staff.email
        #     email_msg = EmailMessage(subject, mail_message, to=[to_email])
        #     email_msg.send()
        #     notify.send(
        #             order, recipient=staff, verb='A new order has been placed.',
        #             action_object=order, description='order')
        # return super().form_valid(form)


    def form_invalid(self, form):
        user = self.get_object()
        print(form.errors,"sdaas")
        return super().form_invalid(form)


class ConfirmOrder(FormView):
    template_name = 'frontend/payment.html'
    form_class = ConfirmOrderForm
    model = Order

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            print('here')
            my_cart = Cart.objects.filter(
                user=self.request.user, deleted_at__isnull=True, products__is_ordered=False)
            print(my_cart)
        else:
            print(self.request.session['user'])
            my_cart = Cart.objects.filter(
                user_id=self.request.session['user'], deleted_at__isnull=True, products__is_ordered=False)
        print(my_cart,"ssss")
        context['home'] = False
        context['cart_list'] = my_cart   
        context['sub_total'] = sub_total(my_cart) 
        return context

    def form_valid(self, form):
        user = User.objects.filter(is_superuser=True).first()
        if self.request.user.is_authenticated:
            ordered_by = self.request.user
        else:
            ordered_by = User.objects.get(id=self.request.session['user'])
        print(ordered_by, "aaa")
        my_cart = Cart.objects.filter(
            user=ordered_by, deleted_at__isnull=True, products__is_ordered=False)
            # .exclude(
            #     products__products__quantity__lte=0)
        print(Cart.objects.filter(user=ordered_by))
        queryset = my_cart
        print(queryset,'nkjdnajkdnjkasnkj')
        if queryset.exists():      
            form.instance.user = ordered_by
            code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
            form.instance.code = code
            form.instance.condition_status = Status.objects.get(name='Order Placed')
            
            obj = form.save()
            for prod in queryset:
                prod.deleted_at = timezone.now()
                prod.save()
                obj.products.add(prod.products.id)
                obj.total += prod.products.quantity * prod.products.products.grand_total
                # try:
                #     obj.payment_type = self.request.POST.get('payment_type')
                # except:
                #     obj.payment_type = 'Cash On Delivery'
                # code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
                # obj.code = code
                obj.payment_type = 'Cash On Delivery'
                obj.save()
                try:
                    wl_obj = Wishlist.objects.get(
                        user=ordered_by, products=prod.products, deleted_at__isnull=True)
                    wl_obj.delete()
                except Wishlist.DoesNotExist:
                    pass
                prod.products.is_ordered = True
                prod.products.save()
            for prod in obj.products.all():
                try:
                    prod_obj = Product.objects.get(id=prod.products.id)
                    print(prod_obj.quantity)
                    prod_obj.quantity = int(prod_obj.quantity) - prod.quantity
                    prod_obj.save()
                except Product.DoesNotExist:
                    pass
            track = Tracker.objects.create(order=obj)
            track.status.add(obj.condition_status)
            track.save()
            if 'into_cart' in self.request.session:
                del self.request.session['into_cart']
            if 'user' in self.request.session:
                del self.request.session['user']
            
            # current_site = get_current_site(self.request)
            # message = render_to_string('confirmation_for_order.html', {
            #     'user': ordered_by, 
            #     'domain': CURRENT_DOMAIN,
            #     'uid': urlsafe_base64_encode(force_bytes(ordered_by.pk)),
            #     'token': account_activation_token.make_token(ordered_by),
            #     'oid': obj.id,
            #     'order': obj,
            #     'tracking_code': code
            # })
            # mail_subject = 'BreadFruit Electronics: Orders confirmed'
            # to_email = ordered_by.email
            # email = EmailMessage(mail_subject, message, to=[to_email])
            # # time.sleep(15)

            # email.send()
            notify.send(
                user, recipient=ordered_by, verb='You have ordered something', action_object=obj,
                description='order')
            messages.success(self.request,"Thank You!!! Your order has been placed. See You Soon...")
            return HttpResponseRedirect(reverse('account:test'))
        else:
            return HttpResponseRedirect(reverse('account:test'))

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['user'] = self.request.user
    #     return context


class ConfirmOrderWithCoupon(CreateView):
    template_name = 'layouts/frontend/confirm_order.html'
    form_class = ConfirmOrderForm
    model = Order
    success_url = reverse_lazy('account:test')

    def dispatch(self, *args, **kwargs):
        self.coupon = Coupon.objects.get(id=self.kwargs['coupon_id'])
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        user = User.objects.filter(is_superuser=True).first()
        ordered_by = self.request.user
        my_cart = Cart.objects.filter(
            user=ordered_by, deleted_at__isnull=True, products__is_ordered=False).exclude(
                products__products__quantity__lte=0)
        queryset = my_cart
        if queryset.exists():
            form.instance.user = ordered_by
            form.instance.code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
            obj = form.save()
            for prod in queryset:
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
                obj.total = obj.total - self.coupon.discount_amount
            elif self.coupon.discount_percent:
                obj.total = obj.total - ((obj.total * self.coupon.discount_percent)/100)
            else:
                obj.total = obj.total
            obj.save()
            if self.coupon.user:
                self.coupon.is_used = True
            else:
                self.coupon.validity_count -= 1
                if self.coupon.validity_count == 0:
                    self.coupon.is_used = True
            self.coupon.save()

            if 'into_cart' in self.request.session:
                del self.request.session['into_cart']
            current_site = get_current_site(self.request)
            message = render_to_string('confirmation_for_order.html', {
                'user': ordered_by, 
                'domain': CURRENT_DOMAIN,
                'uid': urlsafe_base64_encode(force_bytes(ordered_by.pk)),
                'token': account_activation_token.make_token(ordered_by),
                'oid': obj.id
            })
            mail_subject = 'BreadFruit Electronics: Orders confirmed '
            to_email = ordered_by.email
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            notify.send(
                user, recipient=obj.user, verb='You have ordered something', action_object=obj,
                description='order')
            return HttpResponseRedirect(reverse('cart:my_order_detail', kwargs={'pk': obj.pk }))
        else:
            pass
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['coupon'] = self.coupon
        context['user'] = self.request.user
        return context


def confirmation(request, uidb64, token, order):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        order = Order.objects.get(id=order)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        order.is_confirmed = True
        order.save()
        tracker = Tracker.objects.get(order=order)
        # staffs = Staff.objects.filter(deleted_at=None)
        # subject = 'New order'
        # mail_message = 'New Order has been placed. Please Review' 
        # for staff in staffs:
        #     to_email = staff.email
        #     email_msg = EmailMessage(subject, mail_message, to=[to_email])
        #     email_msg.send()
        #     notify.send(
        #             order, recipient=staff, verb='A new order has been placed.',
        #             action_object=order, description='order')

        admin_user = User.objects.filter(is_superuser=True).first()
        notify.send(
            order, recipient=admin_user, verb='A new order has been placed.',
            action_object=order, description='order')

        return HttpResponseRedirect('/tracking-result/'+ str(tracker.id))
    else:
        return HttpResponse('Confirmation link is invalid!')


class WishListProductDetail(ClientMixin, DetailView):
    template_name = 'layouts/frontend/product.html'
    model = Product    

    def dispatch(self, *args, **kwargs):
        self.product = Product.objects.get(id=self.kwargs['pk'])
        return super().dispatch(*args, **kwargs)

    def similar_prodts(self):
        categories = self.product.categories.all()
        for these in categories:
            qs = Product.objects.filter(categories=these)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['similar_products'] = self.similar_prodts()
        context['form'] = RatingForm
        context['quantity_form'] = QuantityForm
        return context


class CartList(ClientMixin, ListView):
    template_name = 'layouts/frontend/cartlist.html'

    def queryset(self):
        if self.request.user.is_authenticated:
            my_cart = Cart.objects.filter(
                user=self.request.user, deleted_at__isnull=True, products__is_ordered=False)
            queryset = my_cart
        else:
            my_cart = []
            if 'into_cart' in self.request.session:
                for obj_id in self.request.session['into_cart']:
                    obj = Cart.objects.get(id=obj_id)
                    my_cart.append(obj)
            queryset = my_cart
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['home'] = False
        return context


class MyAllOrders(LoginRequiredMixin, ClientMixin, ListView):
    template_name = 'frontend/myorders.html'

    def get_queryset(self):
        queryset = Order.objects.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['home'] = False
        # ordered_products = Order.objects.filter(deleted_at__isnull=True).first()
        total = 0
        
        # for prod in ordered_products.products.filter(user=self.request.user):
        #     total = total + prod.products.grand_total * prod.quantity
        # context['total'] = total
        # return context
        return context

class MyOrderDetail(LoginRequiredMixin, ClientMixin, DetailView):
    template_name = 'frontend/order_detail.html'
    model = Order
    login_url = "/accounts/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ordered = self.get_object().products.first()
        context['ordered_products'] = ordered.productrefund_set.all()
        ordered_products = self.get_object().products.all()
        sub_total = 0
        for prod in ordered_products:
            sub_total = sub_total + prod.products.grand_total * prod.quantity
        grand_total = self.get_object().total
        context['total'] = grand_total
        if sub_total > grand_total:
            context['discount_amount'] = sub_total - grand_total
        totalrefund = 0
        for refund in self.get_object().refund.all():
            totalrefund = totalrefund + int(refund.quantity) * float(refund.products.products.grand_total)
        context['totalrefund'] = totalrefund
        return context

class CancelOrder(LoginRequiredMixin, ClientMixin, UpdateView):
    template_name = 'layouts/frontend/cancelorder.html'
    model = Order
    form_class = CancelOrderForm
    success_url =reverse_lazy('cart:my_orders')

    def post(self, request, **kwargs):
        obj = get_object_or_404(Order, id=self.kwargs['pk'])
        obj.condition_status = Status.objects.filter(name ="Cancelled").first()
        for pit in obj.products.all():
            pit.products.quantity = pit.products.quantity + pit.quantity
            pit.products.save()
        obj.save()
        return HttpResponseRedirect(reverse_lazy('cart:my_orders'))

    # def post()
class ClientOrderDetail(LoginRequiredMixin, ClientMixin, DetailView):
    template_name = 'layouts/frontend/order_detail.html'
    model = Order
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        for n in self.request.user.notifications.unread():
            if n.action_object == self.get_object():
                n.mark_as_read();
        return super(ClientOrderDetail, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ordered_products = self.get_object().products.all()
        total = 0
        for prod in ordered_products:
            total = total + prod.products.grand_total
        context['total'] = total
        return context



class ClientCouponDetail(LoginRequiredMixin, ClientMixin, DetailView):
    template_name = 'layouts/frontend/coupon_detail.html'
    model = Coupon
    login_url = "/accounts/login/"

    def dispatch(self, request, *args, **kwargs):
        for n in self.request.user.notifications.unread():
            if n.action_object == self.get_object():
                n.mark_as_read();
        return super(ClientCouponDetail, self).dispatch(request, *args, **kwargs)


class MyCoupons(LoginRequiredMixin, ClientMixin, ListView):
    template_name = 'layouts/frontend/users_coupons.html'

    def get_queryset(self):
        queryset = Coupon.objects.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['home'] = False
        return context


class NewProductList(ClientMixin, ListView):
    template_name = 'layouts/frontend/new_products.html'

    def get_queryset(self):
        queryset_list = Product.objects.filter(
            deleted_at__isnull=True, is_new=True)
        paginator = Paginator(queryset_list, 12)

        page = self.request.GET.get('page')
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        return queryset


class SpecialProductList(ClientMixin, ListView):
    template_name = 'layouts/frontend/special_products.html'

    def get_queryset(self):
        queryset_list = Product.objects.filter(
            deleted_at__isnull=True, is_on_sale=True)
        paginator = Paginator(queryset_list, 12)

        page = self.request.GET.get('page')
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        return queryset


class ComingProductList(ClientMixin, ListView):
    template_name = 'layouts/frontend/upcoming_products.html'

    def get_queryset(self):
        queryset_list = Product.objects.filter(
            deleted_at__isnull=True, is_coming_soon=True)
        paginator = Paginator(queryset_list,12)

        page = self.request.GET.get('page')
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        return queryset


class TagsProductListView(ClientMixin, ListView):
    template_name = 'layouts/frontend/tags_products.html'
    queryset = Product.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tagsobjects = get_object_or_404(Tag, title=self.kwargs['slug'])
        context['tag_title'] = tagsobjects.title
        queryset_list = Product.objects.filter(
            deleted_at__isnull=True, tags=tagsobjects)
        paginator = Paginator(queryset_list, 12)

        page = self.request.GET.get('page')
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        context['object_list'] = queryset
        return context


class DeliveryView(ClientMixin, TemplateView):
    template_name = "layouts/frontend/delivery.html"


class TermsAndConditionsView(ClientMixin, TemplateView):
    template_name = "layouts/frontend/terms_and_conditions.html"


class AboutusView(ClientMixin, TemplateView):
    template_name = 'layouts/frontend/about.html'


class OurStoresView(ClientMixin, TemplateView):
    template_name = 'layouts/frontend/ourstores.html'



# rating views
class GetProductRate(View):

    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['prod_id'])
        ratings = Rating.objects.filter(product__id=product.id)
        if ratings.exists():
            total_rating = 0
            count = ratings.count()
            for rate in ratings:
                total_rating += rate.rate
            rating_avg = total_rating / count
            rate = rating_avg
        else:
            rate = 0
        return JsonResponse({'rate': rate})


class CreateRating(LoginRequiredMixin, FormView):
    template_name = 'cart/product_detail.html'
    model = Rating
    success_url = '/'
    form_class = RatingForm

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=self.kwargs['prod_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            rating = Rating.objects.get(
                user=self.request.user, product=self.product)
            rating.rate = form.cleaned_data['rate']
            rating.review = form.cleaned_data['review']
            rating.save()
        except Rating.DoesNotExist:
            form.instance.user = self.request.user
            form.instance.product = self.product
            form.save()            
        return super().form_valid(form)


# Compare Products
class AddToCompare(View):

    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['prod_id'])
        if not 'compare' in request.session or not request.session['compare']:
            request.session['compare'] = [product.id]
            status = True
        else:
            saved_list = request.session['compare']
            if product.id in saved_list:
                saved_list = self.request.session['compare']
                saved_list.remove(product.id)
                request.session['compare'] = saved_list 
                status = False
            else:
                saved_list.append(product.id)
                request.session['compare'] = saved_list
                status = True
                if len(saved_list) > 3:
                    del saved_list[0]
                    request.session['compare'] = saved_list
        return JsonResponse({'is_incompare': status}, status=200)


class GetComparingProducts(ClientMixin, TemplateView):
    template_name = 'layouts/frontend/product_compare.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not 'compare' in self.request.session or not self.request.session['compare']:
            context['object_list'] = []
        else:
            compare_list = self.request.session['compare']
            qs = []
            for prod_id in compare_list:
                product = get_object_or_404(Product, id=prod_id)
                qs.append(product)
            context['object_list'] = qs
        return context    


class GetProductsInCompare(View):
    def get(self, request, **kwargs):
        compare_list = []
        if not 'compare' in self.request.session or not self.request.session['compare']:
            compare_list = compare_list
        else:
            compare_list = self.request.session['compare']
        return JsonResponse({'compare_list': compare_list})


class GetComparing(View):

    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['prod_id'])
        if not 'compare' in self.request.session or not self.request.session['compare']:
            status = False
        else:
            compare_list = self.request.session['compare']
            for prod_id in compare_list:
                product_in_session = get_object_or_404(Product, id=prod_id)
                if product.id == product_in_session.id:
                    status = True
                else:
                    status = False
        return JsonResponse({'is_incompare': status})


class RemoveFromCompare(View):

    def get(self, request, **kwargs):
        product = get_object_or_404(Product, pk=kwargs['prod_id'])
        compare_list = self.request.session['compare']
        compare_list.remove(product.id)
        request.session['compare'] = compare_list        
        return HttpResponseRedirect(reverse("cart:compare_products"))


class UpdateQuantity(View):

    def post(self, request, **kwargs):

        pit = get_object_or_404(ProductInTransaction, pk=kwargs['prod_id'])
        pit.quantity = json.loads(self.request.POST['quantity'])
        pit.save()
        if self.request.user.is_authenticated:
            cart_list = Cart.objects.filter(user=request.user, products__is_ordered=False, deleted_at__isnull=True)
        else:
            try:
                cart_list = Cart.objects.filter(id__in=self.request.session['into_cart'],products__is_ordered=False, deleted_at__isnull=True)
            except:
                cart_list = Cart.objects.filter(user_id=self.request.session['user'],products__is_ordered=False,  deleted_at__isnull=True)
        print(cart_list.values_list('products__products__name', flat=True), "aassasaa")
        cart_list = cart_list.order_by('created_at')
        x = render_to_string('frontend/cart-items.html',
            {'cart_list': cart_list, 'sub_total':sub_total(cart_list)})
        return HttpResponse(x)


class CheckoutDirectly(ClientMixin, View):

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product, id=self.kwargs['prod_id'])
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        if request.user.is_authenticated:
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
            return HttpResponseRedirect(reverse("cart:checkout"))
        else:
            prod_in_tran = ProductInTransaction.objects.create(
                products=self.product)
            obj = Cart.objects.create(
                products=prod_in_tran)
            if not 'into_cart' in request.session or not request.session['into_cart']:
                request.session['into_cart'] = [obj.id]
            else:
                saved_list = request.session['into_cart']
                saved_list.append(obj.id)
                request.session['into_cart'] = saved_list
            return HttpResponseRedirect(reverse("cart:checkout"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product'] = self.product
        context['home'] = False
        context['form'] = GuestForm()
        return context


class Checkout(ClientMixin, FormView):
    template_name = 'frontend/checkout.html'
    model = User
    success_url = reverse_lazy('cart:payment')

    def get_form_class(self):
        if self.request.user.is_authenticated:
            data = User.objects.get(id = self.request.user.pk)
            userform = UserForm(initial=data.__dict__)
            userform.instance.email = self.request.user.email
            return UserForm
        else:
            return GuestForm
            

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            data = User.objects.get(id = self.request.user.pk)
            context['data'] = data
            form = UserForm(initial=data.__dict__)
            form.instance.email = self.request.user.email
            context['form'] = form
            my_cart = Cart.objects.filter(
                user=self.request.user, deleted_at__isnull=True, products__is_ordered=False)
        else:
            context['form'] = GuestForm()
            my_cart = []
            if 'into_cart' in self.request.session:
                for obj_id in self.request.session['into_cart']:
                    obj = Cart.objects.get(id=obj_id)
                    my_cart.append(obj)
        context['home'] = False
        
        # if self.request.user.is_authenticated:
        #     context['cform'] = CouponApplyForm
        #     context['coupons'] = Coupon.objects.filter(user=self.request.user)
        #     context['total'] = self.total
        #     context['home'] = False
        #     context['validation'] = self.validation
        #     context['applicable'] = self.applicable
        #     context['grand_total'] = self.grand_total
        #     context['payment'] = PaymentForm()

        #     if self.validation:
        #         context['coupon'] = self.coupon_obj
        #     if self.request.user.street_name and self.request.user.contact_no1:
        #         context['applicable'] = True
        #     else:
        #         context['applicable'] = False  
        context['cart_list'] = my_cart   
        context['sub_total'] = sub_total(my_cart) 
        return context

    def form_valid(self, form):
        print(form.cleaned_data)
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
       

        if self.request.user.is_authenticated:
            user = self.request.user
            user.first_name = first_name
            user.last_name = last_name
            user.save
        else:
            email = form.cleaned_data['email']
            user, created = User.objects.get_or_create(username=email, email=email)
            mobile_number = form.cleaned_data['mobile_number']
            street_name = form.cleaned_data['street_name']
            email = form.cleaned_data['email']
            city = form.cleaned_data['city']
            country = form.cleaned_data['country']
            postal_code = form.cleaned_data['postal_code']
            user.first_name = first_name
            user.last_name = last_name
            user.mobile_number = mobile_number
            user.email = email
            user.customer_type='Guest'
            user.is_active = False
            user.save()
            

            shipping_addr = ShippingAddress.objects.get_or_create(user=user, country=country, city=city, street_name=street_name,
                postal_code=postal_code)
            

        if 'into_cart' in self.request.session:
            my_cart = []
            for obj_id in self.request.session['into_cart']:
                obj = Cart.objects.get(id=obj_id)
                obj.user = user
                obj.products.user = user
                obj.save()
                my_cart.append(obj)
            self.request.session['user'] = user.id
            del self.request.session['into_cart']
        

        

        # else:
        #     queryset = Cart
        # code= ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
        # order = Order.objects.create(user=user, code= code)
        # staffs = Staff.objects.filter(deleted_at=None)
        # subject = 'New order'
        # mail_message = 'New Order has been placed. Please Review' 
        # for staff in staffs:
        #     to_email = staff.email
        #     email_msg = EmailMessage(subject, mail_message, to=[to_email])
        #     email_msg.send()
        #     notify.send(
        #             order, recipient=staff, verb='A new order has been placed.',
        #             action_object=order, description='order')

        # admin_user = User.objects.filter(is_superuser=True).first()
        # notify.send(
        #             order, recipient=admin_user, verb='A new order has been placed.',
        #             action_object=order, description='order')

        # for prod in queryset:
        #     order.products.add(prod.products.id)
        #     order.total += prod.products.quantity * prod.products.products.grand_total
        #     # code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
        #     # order.code = code
        #     order.save()
        #     prod.products.is_ordered = True
        #     prod.products.save()
        # Tracker.objects.create(order=order)
        # if 'into_cart' in self.request.session:
        #     del self.request.session['into_cart']
        # current_site = get_current_site(self.request)
        # message = render_to_string('confirmation_for_order.html', {
        #     'user': user, 
        #     'domain': CURRENT_DOMAIN,
        #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        #     'token': account_activation_token.make_token(user),
        #     'oid': order.id,
        #     'order': order,
        #     'tracking_code': code
        # })
        # mail_subject = 'BreadFruit Electronics: Orders confirmed'
        # to_email = user.email
        # email = EmailMessage(mail_subject, message, to=[to_email])
        # email.send()
        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors,"ssscsdckamcklndckndk")
        return super().form_invalid(form)


# class ConfirmOrder(ClientMixin, CreateView):
#     template_name = 'frontend/payment.html'
#     form_class = ConfirmOrderForm
#     model = Order
#     success_url = reverse_lazy('cart:my_orders')

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         if self.request.user.is_authenticated:
#             data = User.objects.get(id = self.request.user.pk)
#             my_cart = Cart.objects.filter(
#                 user=self.request.user, deleted_at__isnull=True, products__is_ordered=False)
#         else:
#             my_cart = []
#             if 'into_cart' in self.request.session:
#                 for obj_id in self.request.session['into_cart']:
#                     obj = Cart.objects.get(id=obj_id)
#                     my_cart.append(obj)
#         context['home'] = False
        
#         # if self.request.user.is_authenticated:
#         #     context['cform'] = CouponApplyForm
#         #     context['coupons'] = Coupon.objects.filter(user=self.request.user)
#         #     context['total'] = self.total
#         #     context['home'] = False
#         #     context['validation'] = self.validation
#         #     context['applicable'] = self.applicable
#         #     context['grand_total'] = self.grand_total
#         #     context['payment'] = PaymentForm()

#         #     if self.validation:
#         #         context['coupon'] = self.coupon_obj
#         #     if self.request.user.street_name and self.request.user.contact_no1:
#         #         context['applicable'] = True
#         #     else:
#         #         context['applicable'] = False  
#         context['cart_list'] = my_cart   
#         context['sub_total'] = sub_total(my_cart) 
#         return context

#     def form_valid(self, form):
#         user = User.objects.filter(is_superuser=True).first()
#         ordered_by = self.request.user
#         my_cart = Cart.objects.filter(
#             user=self.request.user, deleted_at__isnull=True, products__is_ordered=False).exclude(
#                 products__products__quantity__lte=0)

#         queryset = my_cart
#         if queryset.exists():      
#             form.instance.user = ordered_by
#             code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
#             form.instance.code = code
#             form.instance.condition_status = Status.objects.get(name='Ordered')
            
#             obj = form.save()
#             for prod in queryset:
#                 # prod.deleted_at = timezone.now()
#                 # prod.save()
#                 obj.products.add(prod.products.id)
#                 obj.total += prod.products.quantity * prod.products.products.grand_total
#                 obj.payment_type = self.request.POST.get('payment_type')
#                 # code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
#                 # obj.code = code
#                 obj.save()
#                 try:
#                     wl_obj = Wishlist.objects.get(
#                         user=ordered_by, products=prod.products, deleted_at__isnull=True)
#                     wl_obj.delete()
#                 except Wishlist.DoesNotExist:
#                     pass
#                 prod.products.is_ordered = True
#                 prod.products.save()
#             for prod in obj.products.all():
#                 try:
#                     prod_obj = Product.objects.get(id=prod.products.id)
#                     prod_obj.quantity -= prod.quantity
#                     prod_obj.save()
#                 except Product.DoesNotExist:
#                     pass
#             track = Tracker.objects.create(order=obj)
#             track.status.add(obj.condition_status)
#             track.save()
#             if 'into_cart' in self.request.session:
#                 del self.request.session['into_cart']
#             # current_site = get_current_site(self.request)
#             # message = render_to_string('confirmation_for_order.html', {
#             #     'user': ordered_by, 
#             #     'domain': CURRENT_DOMAIN,
#             #     'uid': urlsafe_base64_encode(force_bytes(ordered_by.pk)),
#             #     'token': account_activation_token.make_token(ordered_by),
#             #     'oid': obj.id,
#             #     'order': obj,
#             #     'tracking_code': code
#             # })
#             # mail_subject = 'BreadFruit Electronics: Orders confirmed'
#             # to_email = ordered_by.email
#             # email = EmailMessage(mail_subject, message, to=[to_email])
#             # # time.sleep(15)
#             # email.send()
#             notify.send(
#                 user, recipient=ordered_by, verb='You have ordered something', action_object=obj,
#                 description='order')
#             messages.success(self.request,"Thank You!!! Your order has been placed. See You Soon...")
#             return HttpResponseRedirect(reverse('cart:my_order_detail', kwargs={'pk': obj.pk }))
#         else:
#             pass

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['user'] = self.request.user
#         return context


class TrackOrder(ClientMixin, TemplateView):
    template_name = 'cart/track.html'


class TrackingResultProcessing(ClientMixin, TemplateView):
    template_name = 'frontend/tracker_result.html'

    def get(self, request, *args, **kwargs):
        code = self.request.GET.get('code')
        try:
            obj = Tracker.objects.get(order__code=code)
            return HttpResponseRedirect('/tracking-result/'+ str(obj.id))
        except Tracker.DoesNotExist:
            return HttpResponseRedirect('/tracking-result/')


class TrackingResult(ClientMixin, TemplateView):
    template_name = 'frontend/tracker_result.html'

    def dispatch(self, request, *args, **kwargs):
        tracker = self.kwargs.get('tracker_id', None)
        try:
            self.tracker = Tracker.objects.get(id=tracker)
        except Tracker.DoesNotExist:
            self.tracker = None
        return super(TrackingResult, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(TrackingResult, self).get_context_data(**kwargs)
        context['object'] = self.tracker
        return context



class NotificationList(ClientMixin, ListView):
    template_name = 'cart/notification.html'

    def get_queryset(self):
        queryset = Notification.objects.filter(recipient=self.request.user)
        paginator = Paginator(queryset, 20)

        page = self.request.GET.get('page')
        try:
            queryset = paginator.page(page)
        except PageNotAnInteger:
            queryset = paginator.page(1)
        except EmptyPage:
            queryset = paginator.page(paginator.num_pages)
        return queryset


class InquiryCreate(CreateView):
    template_name = 'cart/inquiry_form.html'
    model = Inquiry
    form_class = InquiryForm
    success_url = reverse_lazy("account:test")

    def form_valid(self, form):
        form.save()
        return super(InquiryCreate, self).form_valid(form)


class QuickView(ClientMixin, DetailView):
    template_name = 'cart/quickview.html'
    model = Product

    def get_context_data(self, **kwargs):
        context = super(QuickView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            try:
                rated = Rating.objects.get(user=self.request.user, product=self.get_object().id)
                context['rated'] = rated
            except Rating.DoesNotExist:
                pass

        product = self.get_object().id
        context['variant'] = self.get_object().variant.all()

        if self.request.user.is_authenticated:
            try:
                prod_in_tran = ProductInTransaction.objects.get(
                    user=self.request.user, products=product, is_ordered=False, deleted_at__isnull=True)
                try:
                    cart = Cart.objects.get(
                        products=prod_in_tran, user=self.request.user, deleted_at__isnull=True)
                    status = True
                    context['pit'] = int(cart.products.quantity)
                except Cart.DoesNotExist:
                    status = False
            except ProductInTransaction.DoesNotExist:
                status = False
            try:
                rview = RecentlyViewed.objects.get(user=self.request.user)
                if rview.products.all().count() > 4:
                    rview.products.remove(rview.products.last())
                rview.products.add(self.get_object())
            except RecentlyViewed.DoesNotExist:
                rview = RecentlyViewed.objects.create(user=self.request.user)
                rview.products.add(self.get_object())
        else:
            if not 'into_cart' in self.request.session or not self.request.session['into_cart']:
                status = False
            else:
                cart_list = self.request.session['into_cart']
                try:
                    cart = Cart.objects.get(
                        id__in=cart_list, deleted_at__isnull=True, products__products__id=product)
                    status = True
                    context['pit'] = int(cart.products.quantity)                       
                except Cart.DoesNotExist:
                    status = False
        if status:
            context['cart'] = cart
        context['status'] = status

        return context


from django.db.models import Count


class TestView(TemplateView):
    template_name="layouts/frontend/test.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # all_coupons = Coupon.objects.values('code').annotate(Count('id')).order_by().filter(id__count__gt=1)
        # coupons = Coupon.objects.filter(code__in=[coupon['code'] for coupon in all_coupons])
        # for coupon in coupons:
        #     coupon.code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
        #     coupon.save()
        # all_orders = Order.objects.all()
        # # orders = Order.objects.filter(code__in=[order['code'] for order in all_orders])
        # for order in all_orders:
        #     order.code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
        #     order.save()
        # context['orders'] = all_orders
        # context['ads'] = Advertisement.objects.all()
        # user = User.objects.get(username='Deep9')
        # user.username = 'Deep9@'
        # user.save()
        return context

class RunView(View):
    def get(self, request, *args, **kwargs):
        pass


class ShopView(ClientMixin, ListView):
    template_name="frontend/shop.html"
    model = Product
    queryset = Product.objects.filter(deleted_at=None)


class OurStoryView(ClientMixin, TemplateView):
    template_name="frontend/story.html"


class SustainabilityView(ClientMixin, TemplateView):
    template_name="frontend/sustainability.html"