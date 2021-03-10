import socket
import datetime
import json
import random
from random import choice
import math as m
from django.core.mail import send_mail
import string
import re
from django.contrib.auth import authenticate, login, logout
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
from rest_framework.generics import UpdateAPIView, CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT
from rest_framework.views import APIView
from .serializers import *
from account.tokens import account_activation_token
from cart.models import (Cart, Category, FeaturedProduct, Order, Product,Story,File,
                         ProductInTransaction, Rating, Tracker, Wishlist, Photo,SubCategory,SubCategoryMapping)
from account.models import User,ShippingAddress
from django.contrib.auth.hashers import make_password
from rest_framework.authtoken.models import Token
from .authentications import CustomTokenAuth
from gaava import settings
from .sms_send import sendSms


def OTPGen():
    string = '123456789'
    OTP = ""
    varlen = len(string)
    for i in range(6):
        OTP += string[m.floor(random.random() * varlen)]
    return OTP


class UserRegisterAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    

    def post(self, request, *args, **kwargs):
        otp = OTPGen()
        serializer = UserRegistrationSerializer(data=request.data)
        admin_user = User.objects.filter(is_superuser=True).first()
        if serializer.is_valid():
            code = otp
            new_data = serializer.data
            email = new_data['email']
            username = email.split('@')[0]
            if User.objects.filter(username=username).first():
                chars = string.digits
                modified_username=username + ''.join(choice(chars) for _ in range(2))
                username = modified_username
                user=User.objects.create(
                    email=new_data['email'], username=modified_username,
                    mobile_number=new_data['mobile_number']
                )
            else:
                user=User.objects.create(
                    email=new_data['email'], username=username,
                    mobile_number=new_data['mobile_number'])
            user.set_password(new_data['password'])
            user.is_active = False
            token, create = Token.objects.get_or_create(user=user)
            user.otp_code = int(code)
            # sendSms.sendsms(self, code, new_data['mobile_number'])
            user.save()
            grp = Group.objects.get(name='Customer')
            grp.user_set.add(user)
            valid_from = datetime.datetime.today()
            valid_to = datetime.datetime.today() + datetime.timedelta(days=60)
            dict = {}
            dict['email'] = new_data['email']
            dict['id'] = user.pk
            dict['username'] = username
            dict['mobile_number'] = new_data['mobile_number']
            dict['token'] = token.key
            dict['otp_code'] = code
            return Response({"code": 200, "status": "success", "message": "User Account Created", "details": dict})
        return Response({"code": 400, "status": "failure", "message": "Empty Field", "details": serializer.errors})


class UserVerifyAPIView(APIView):
    permission_classes = [AllowAny]
    # serializer_class = UserVerificationSerializers

    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})

        user_id = usid.user_id

        serializer = UserVerificationSerializers(data=request.data)
        if serializer.is_valid():
            otp = serializer.data['otp']
            if User.objects.filter(id=user_id, otp_code=serializer.data['otp']).exists():
                User.objects.filter(
                    id=user_id, otp_code=otp).update(is_active=True)
                return Response({"code": 200, "status": 'success', "message": "Successfully Verified", "details": "user verified"})
            else:
                return Response({'code': 404, 'status': 'FAILURE', 'message': 'Failure', "details": 'Invalid Credentials'})
        return Response({'code': 404, 'status': 'FAILURE', "message": "Empty Field", "details": serializer.errors})


class UserLoginAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            new_data = serializer.data
            username = new_data['email']
            password = new_data['password']
            
            # using phone number
            if not re.findall("[A-Za-z]",username):
                user = authenticate(
                    mobile_number=username, password=password)
            else:
                user = authenticate(username=username,password=password)
            if user is not None:
                token = Token.objects.filter(user_id=user.id).values('key')
                dict = ['token']
                for tkn in token:
                    pass
                if user.is_active:
                    login(request, user)
                    dict = {}
                    dict['id'] = user.id
                    dict['username']=user.username
                    dict['email'] = user.email
                    dict['mobile_number'] = str(user.mobile_number)
                    dict['token'] = tkn['key']
                    return Response({"code": 200, "status": "Success", "message": "Successfully Logged In", 'details': dict})
                else:
                    return Response({"code": 400, "status": "Failure", "message": "Inactive User"})
            else:
                return Response({"code": HTTP_400_BAD_REQUEST, "status": "failure", "message": "Invalid Credentials"})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": "failure", 'message': 'Empty field', "details": serializer.errors})


class UserUpdateAPIView(APIView):
    permission_classes = [AllowAny]
    serializer_class = UserUpdateSerializers

    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})

        user_id = usid.user_id
        serializer = UserProfileUpdateSerializers(data=request.data)
        if serializer.is_valid():
            new_data = serializer.data
            User.objects.filter(id=user_id).update(username=new_data['username'],
                                                    email=new_data['email'],mobile_number=new_data['mobile_number'])
            return Response({"code": HTTP_200_OK, "status": "success", "message": "Successfully Updated", "details": new_data})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Field", "details": serializer.errors})


class UserUpdateBillingAddressAPIView(APIView):
    serializer_class = UpdateAddressSerializer
    model = User

    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})
        user_id=usid.user_id
        serializer = UpdateAddressSerializer(data=request.data)
        if serializer.is_valid():
            new_data = serializer.data
            if ShippingAddress.objects.filter(user_id=user_id).count()==3:
                return Response({"code": 400, "status": "failure", "message": "Update Unsuccessful", "details":[]})
            
            try:
                if new_data['lat']:
                    address = ShippingAddress.objects.create(user_id=user_id,contact_number=new_data['contact_number'],
                                                postal_code=new_data['postal_code'],city=new_data['city'],name=new_data['name'],country=new_data['country'],
                                                lat=new_data['lat'],lng=new_data['lng'],
                                                street_name=new_data['street_name'])
            except KeyError:
                address = ShippingAddress.objects.create(user_id=user_id,contact_number=new_data['contact_number'],
                                            postal_code=new_data['postal_code'],city=new_data['city'],name=new_data['name'],country=new_data['country'],
                                            street_name=new_data['street_name'])
            data = ShippingAddress.objects.filter(user_id=user_id).values()
            toret=[]
            for resp in data:
                dicti={}
                dicti['id']=resp['id']
                dicti['user_id']=resp['user_id']
                dicti['contact_number']=resp['contact_number']
                dicti['postal_code']=resp['postal_code']
                dicti['city']=resp['city']
                dicti['name']=resp['name']
                dicti['street_name']=resp['street_name']
                dicti['country']=resp['country']
                dicti['latitide']=resp['lat']
                dicti['longitude']=resp['lng']
            toret.append(dicti)
            return Response({"code": HTTP_200_OK, "status": "success", "message": "Added successfully", "details": toret})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Field", "details": serializer.errors})


class GetUserShippingAddress(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})
        user_id=usid.user_id
        if ShippingAddress.objects.filter(user_id=user_id).first():
            data = ShippingAddress.objects.filter(user_id=user_id).values()
            toret=[]
            for resp in data:
                dicti={}
                dicti['id']=resp['id']
                dicti['user_id']=resp['user_id']
                dicti['contact_number']=resp['contact_number']
                dicti['country']=resp['country']
                dicti['postal_code']=resp['postal_code']
                dicti['city']=resp['city']
                dicti['street_name']=resp['street_name']
                dicti['name']=resp['name']
                dicti['latitide']=resp['lat']
                dicti['longitude']=resp['lng']
                toret.append(dicti)
            return Response({"code": HTTP_200_OK, "status": "success", "message": "Fetehed Successfully", "details": toret})
        return Response({"code": 200, "status": "success", "message": "Empty Address", "details": []})


class LogoutAPIView(APIView):
    def post(self, request):
        logout(request)
        return Response({"code": HTTP_200_OK, "status": "success", "message": "Successfully Logged Out", "details": "successfully logout"})


class ProductList(APIView):
    def get(self, request, *args, **kwargs):
        uri = socket.gethostbyname(socket.gethostname())
        products = Product.objects.filter(deleted_at = None).values('id', 'likes', 'name', 'product_address','slug', 'description', 'discount_percent', 'unit',
                                                'summary','warning', 'visibility', 'quantity', 'old_price', 'price', 'categories')
        toret = []
        for details in products:
            dict = {}
            product_id = details['id']
            product_name = details['name']
            product_address=details['product_address']
            product_price = details['price']
            product_unit = details['unit']
            product_stock = details['quantity']
            for category in products:
                cat ={}
                name = Category.objects.filter(id=details['categories']).values('id','title','image')
                for one in name:
                    cat['category']=one['title']
                    dict.update(cat)
            product_discount = details['discount_percent']
            likes = details['likes']
            dict['id'] = product_id
            dict['name'] = product_name
            uri = 'http://'+uri+':8000'+'/media/'
            images = Photo.objects.filter(product=product_id).values('photo')
            dict['product_image'] = []
            dict['product_likes'] = likes
            dict['from'] = product_address
            for image in images:
                dict['image']='http://localhost:8000/media/'+image['photo']
                dict['product_image'].append('http://localhost:8000/media/'+image['photo'])
            dict['quantity'] = product_stock
            dict['description'] = details['description']
            dict['product_discount'] = str(product_discount)+''+'%'
            dict['old_price'] = product_price
            new_price = (product_price/100.0)*product_discount
            total_price = product_price-new_price
            dict['unit'] = product_unit
            dict['product_price'] = total_price
            toret.append(dict)
        return JsonResponse({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toret})


class CategoryList(APIView):
    def get(self, request, *args, **kwargs):
        uri = socket.gethostbyname(socket.gethostname())
        toret = []
        sub_cat = SubCategoryMapping.objects.all().values()
        for category in sub_cat:
            sub_cat = Category.objects.filter(id=category['id']).values('id','image','title')
            dict = {}
            for sub_cats in sub_cat:
                dict['id'] = sub_cats['id']
                dict['title'] = sub_cats['title']
                dict['image'] = 'http://localhost:8000/media/'+str(sub_cats['image'])
                sub_cat = SubCategory.objects.filter(id=sub_cats['id']).values('name')
                for sub_name in sub_cat:
                    dict['sub_category'] = []
                    det = {}
                    det['sub_category'] = sub_name
                    dict['sub_category'].append(det['sub_category'])
            toret.append(dict)
        return Response({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toret})

    def post(self, request, *args, **kwargs):
        serializer = ProductIDSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            category = Category.objects.filter(
                title=data['category_title']).values('id', 'image', 'title')
            toret = []
            for all_id in category:                
                catid = all_id['id']
                product = Product.objects.filter(categories=all_id['id'],deleted_at=None)
                    
                for details in product:
                    dict = {}
                    product_price = details.price
                    product_discount = details.discount_percent
                    dict['id']=details.id
                    dict['name']=details.name
                    dict['description']=details.description
                    dict['summary']=details.summary
                    dict['warning']=details.warning
                    dict['visibility']=details.visibility
                    dict['likes']=details.likes
                    dict['from']=details.product_address
                    dict['slug']=details.slug
                    dict['image']=[]
                    image = details.photos.all()
                    for img in image:
                        dict['image'].append('http://localhost:8000'+str(img))
                    dict['product_discount']=product_discount
                    dict['old_price']=details.price
                    dict['unit']=details.unit
                    new_price = (product_price/100.0)*product_discount
                    total_price = product_price-new_price
                    dict['quantity']=details.quantity
                    dict['product_address']=details.product_address
                    dict['product_price']=total_price
                    toret.append(dict)
            return Response({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toret})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Field", "details": serializer.errors})


class SingleProductAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = SingleProductSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.data['product_id']
            toret = []
            products = Product.objects.filter(id=product_id, deleted_at=None).values('id', 'likes', 'name', 'slug', 'description', 'discount_percent','product_address',
                                                                    'summary', 'warning', 'visibility', 'quantity', 'old_price', 'price', 'categories')
            for details in products:
                dict = {}
                categories = Category.objects.filter(id=details['categories']).values('title','image')
                
                product_id = details['id']
                for category in categories:
                    name = Category.objects.filter(id=details['categories']).values('id','title','image')
                    for one in name:
                        dict['category']=one['title']
                product_name = details['name']
                product_price = details['price']
                product_stock = details['quantity']
                product_oldPrice = details['old_price']
                product_category = details['categories']
                product_address = details['product_address']
                product_discount = details['discount_percent']
                likes = details['likes']
                dict['id'] = product_id
                dict['name'] = product_name
                uri = 'http://localhost:8000/media/'
                images = Photo.objects.filter(
                    product=product_id).values('photo')
                dict['product_image'] = []
                dict['likes'] = likes
                for image in images:
                    dict['product_image'].append(uri+image['photo'])
                dict['image']=uri+image['photo']
                dict['quantity'] = product_stock
                dict['description'] = details['description']
                dict['product_discount'] = str(product_discount)+''+'%'
                dict['old_price'] = product_oldPrice
                dict['from'] = product_address
                dict['product_price'] = product_price
                new_price = (product_price/100.0)*product_discount
                total_price = product_price-new_price
                dict['total_price'] = new_price
                toret.append(dict)
            return JsonResponse({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toret})
        return JsonResponse({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Field", "details": serializer.errors})


class CartListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        global grand_total
        grand_total = 0
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        toret = []
        if Cart.objects.filter(user_id=user_id).first():
            cart_item = Cart.objects.filter(user_id=user_id).values('products_id','is_ordered','is_taken','is_cancelled','is_completed')
            for cart_status in cart_item:
                cart_details = ProductInTransaction.objects.filter(user=user_id,id=cart_status['products_id']).values(
                'products', 'quantity', 'is_ordered', 'is_taken', 'is_cancelled','created_at','is_completed')
                for cart_product in cart_details:
                    details = Product.objects.filter(id=cart_product['products']).values('id','photos','unit', 'likes', 'name', 'slug', 'description', 'discount_percent','product_address',
                                                        'summary', 'warning', 'visibility', 'quantity', 'old_price', 'price', 'categories')
                    dict = {}
                    dict['id'] = cart_product['products']
                    dict['created_date'] = cart_product['created_at']
                    for price in details:
                        categories = Category.objects.filter(id=price['categories']).values('title','image')
                        for category in categories:
                            name = Category.objects.filter(id=price['categories']).values('id','title','image')
                        for one in name:
                            dict['category']=one['title']
                    dict['name']=price['name']
                    dict['product_discount']=str(price['discount_percent'])+'%'
                    dict['unit'] = price['unit']
                    dict['from'] = price['product_address']
                    dict['product_image']=[]
                    for image in details:
                        image1 = Photo.objects.filter(id=price['photos']).values('photo')
                        for img in image1:
                            dict['image']='http://142.93.221.85/media/'+img['photo']
                            dict['product_image'].append('http://142.93.221.85/media/'+img['photo'])
                    discount = str(price['discount_percent'])
                    dict['product_price'] = price['price']
                    dict['product_quantity'] = cart_product['quantity']
                dict['is_ordered'] = cart_status['is_ordered']
                dict['is_taken'] = cart_status['is_taken']
                dict['is_cancelled'] = cart_status['is_cancelled']
                total={}
                total['grand_total']=[]
                if discount=='0.0':
                    dict['total_price']= price['price']*cart_product['quantity']
                    grand_total += dict['total_price']
                else:
                    total_price = price['price']*cart_product['quantity']
                    discount = (total_price/100)*price['discount_percent']
                    price1 = int(total_price)-int(discount)
                    dict['total_price'] = price1
                    grand_total += dict['total_price']
                total['grand_total']=str(grand_total)
                toret.append(dict)
            return Response({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toret,"grand_total":total['grand_total']})
        return Response({'code': 200, 'status': 'success', 'message': 'Empty Cart', 'details':[]})


class ProductMixin(object):
    def get_product_list(self, request, *args, **kwargs):
        products = Product.objects.filter(deleted_at=None).values('id','likes','name', 'slug', 'description','discount_percent','unit','product_address',
                                                'summary', 'warning', 'visibility', 'quantity', 'old_price', 'price', 'categories')
        toret = []
        for details in products:
            dict = {}
            product_id = details['id']
            product_name = details['name']
            product_price = details['price']
            product_unit= details['unit']
            product_stock = details['quantity']
            product_oldPrice = details['old_price']
            product_address = details['product_address']
            product_discount = details['discount_percent']
            likes = details['likes']
            dict['id'] = product_id
            dict['name'] = product_name
            uri = 'http://142.93.221.85/media/'
            categories = Category.objects.filter(id=details['categories']).values('title','image')
            images = Photo.objects.filter(product=product_id).values('photo')
            dict['product_category'] =[]
            dict['product_image'] = []
            dict['product_likes']=likes
            for image in images:
                dict['product_image'].append(uri+image['photo'])
            for category in categories:
                dict['product_category'].append(category)
            dict['quantity'] = product_stock
            dict['from'] = product_address
            dict['description'] = details['description']
            dict['product_discount'] = str(product_discount)+''+'%'
            dict['old_price'] = product_oldPrice
            dict['unit']=product_unit
            dict['product_price'] = product_price
            new_price = (product_price/100.0)*product_discount
            total_price = product_price-new_price
            dict['with_discount']=total_price
            toret.append(dict)
        return JsonResponse({"code": 200, "status": "success","message": "Successfully Feteched", "details": toret})
            
            
class HomeAPIView(ProductMixin, APIView):
    permissions_classes = (IsAuthenticated,)
    authentication_classes = (CustomTokenAuth,)

    def get(self, request, *args, **kwargs):
        queryset = Product.objects.filter()
        qs = self.get_product_list(queryset)
        return qs


class IncreaseProductInTransaction(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        serializer = SingleProductSerializer(data=request.data)
        user_id = token.user_id
        if serializer.is_valid():
            prod = get_object_or_404(Product, id=serializer.data['product_id'])
            prod_in_tran, created = ProductInTransaction.objects.get_or_create(
                user=user_id, products=prod, is_ordered=False, deleted_at__isnull=True)
            if not created:
                prod_in_tran.quantity += int(prod_in_tran.quantity)
            else:
                prod_in_tran.quantity = int(prod_in_tran.quantity)
            prod_in_tran.save()
            return JsonResponse({'quantity': prod_in_tran.quantity}, status=200)
        return JsonResponse({'message': "Unsuccessful", "status": "failure", 'code': '400', 'details': serializer.errors})


class AddToCartAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        serializer = AddToCartSerializers(data=request.data,many=isinstance(request.data,list))
        if serializer.is_valid():
            for data in serializer.data:
                real_data=dict(data)
                product_id = real_data['product_id']
                product_quantity = real_data['product_quantity']
                user = user_id
                saved = ProductInTransaction.objects.filter(user_id=user_id,products_id=product_id,quantity=product_quantity).update(is_ordered=True)
            return Response({"code": 200, "status": "success","message": "Successfully Added", "details": serializer.data})

        return JsonResponse({'message': "Unsuccessful", "status": "failure", 'code': '400', 'details': serializer.errors})


class CancelListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        if Cart.objects.filter(user=user_id,is_cancelled=True).exists():
            data=Cart.objects.filter(user=user_id,is_cancelled=True).values()
            return Response({"code": 200, "status": "success","message": "Successfully Feteched", "details": data})
        return JsonResponse({"code": 200, "status": "success","message": "Successfully Feteched", "details": 'Not found'})


class OnProgressListAPIView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        if Cart.objects.filter(user=user_id,is_ordered=True).exists():
            data=Cart.objects.filter(user=user_id,is_ordered=True).values()
            return Response({"code": 200, "status": "success","message": "Successfully Feteched", "details": data})
        return JsonResponse({"code": 200, "status": "success","message": "Successfully Feteched", "details": 'Not found'})


class RecentProductAPIView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        if Cart.objects.filter(user=user_id,is_completed=True).first():
            data=Cart.objects.filter(user=user_id,is_completed=True).values()
            return Response({"code": 200, "status": "success","message": "Successfully Feteched", "details": data})
        return JsonResponse({"code": 200, "status": "success","message": "Successfully Feteched", "details": 'Not found'})


class AddToCart(APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        serializer = AddToCartSerializers(data=request.data,many=isinstance(request.data,list))
        if serializer.is_valid():
            for data in serializer.data:
                real_data=dict(data)
                product_id = real_data['product_id']
                product_quantity = real_data['product_quantity']

        product = get_object_or_404(Product, pk=product_id)
        prod_in_tran, created = ProductInTransaction.objects.get_or_create(
            user=user_id, products=product, is_ordered=False, deleted_at__isnull=True)
        try:
            obj = Cart.objects.get(products=prod_in_tran, user=user_id, deleted_at=None)
            status = False
            try:
                wish = Wishlist.objects.get(
                    user=request.user, products__products=product, deleted_at__isnull=False)
                wish.deleted_at = None
                wish.save()
            except Wishlist.DoesNotExist:
                pass
        except Cart.DoesNotExist:
            Cart.objects.create(products=prod_in_tran, user=user_id)
            status = True
            try:
                wish = Wishlist.objects.get(
                    user=user_id, products__products=product, deleted_at__isnull=True)
                wish.deleted_at = timezone.now()
                wish.save()
            except Wishlist.DoesNotExist:
                pass
        return JsonResponse({'is_incart': status}, status=200)


class HomeView(APIView):
   def get(self, request, *args, **kwargs):
        products = Product.objects.all().values('id','likes','name', 'slug', 'description','discount_percent','unit',
                                                'summary', 'warning', 'visibility', 'quantity', 'old_price','product_address', 'price', 'categories')
        toret = []
        for details in products:
            dict = {}
            # page = self.request.query_params.get('page', None)
            product_id = details['id']
            product_name = details['name']
            product_price = details['price']
            product_unit= details['unit']
            likes=details['likes']
            P_addr = details['product_address']
            product_stock = details['quantity']
            product_oldPrice = details['old_price']
            product_discount = details['discount_percent']
            dict['id'] = product_id
            dict['name'] = product_name
            uri = 'http://localhost:8000/media/'
            categories = Category.objects.filter(id=details['categories']).values('title','image')
            for category in categories:
                cat ={}
                name = Category.objects.filter(id=details['categories']).values('id','title','image')
                for one in name:
                    cat['category']=one['title']
                    dict.update(cat)
            images = Photo.objects.filter(product=product_id).values('photo')
            dict['product_image'] = []
            dict['product_likes']=likes
            for image in images:
                dict['image']=uri+image['photo']
                dict['product_image'].append(uri+image['photo'])
            dict['quantity'] = product_stock
            dict['from']=P_addr
            dict['description'] = details['description']
            dict['product_discount'] = str(product_discount)+''+'%'
            dict['old_price'] = product_price
            dict['unit']=product_unit
            new_price = (product_price/100.0)*product_discount
            total_price = product_price-new_price
            dict['product_price']=total_price
            toret.append(dict)

        prod_list=[]
        
        prod_list.append({'product_for_you':[], "sliders": [], "category": []})
        prod_list[0]["product_for_you"] = toret

        sliders = []
        slider= Slider.objects.all().values()
        for sliders1 in slider:
            for_slider={}
            for_slider['id']=sliders1['id']
            if sliders1['slider_type'] == 'product':
                for_slider['product_id'] = sliders1['product_id']
            else:
                for_slider['category_id'] = sliders1['category_id']
            for_slider['title']=sliders1['title']
            for_slider['image']='http://localhost:8000/media/'+sliders1['photos']
            for_slider['url']=sliders1['url']
            for_slider['slider_type']=sliders1['slider_type']
            sliders.append(for_slider)
        prod_list[0]["sliders"] = sliders
        categoryList = []
        sub_cat = SubCategoryMapping.objects.all().values()
        for category in sub_cat:
            sub_cat = Category.objects.filter(id=category['id']).values('id','image','title')
            dict = {}
            for sub_cats in sub_cat:
                dict['id'] = sub_cats['id']
                dict['title'] = sub_cats['title']
                dict['image'] = 'http://localhost:8000/media/'+str(sub_cats['image'])
                sub_cat = SubCategory.objects.filter(id=sub_cats['id']).values('name')
                for sub_name in sub_cat:
                    dict['sub_category'] = []
                    det = {}
                    det['sub_category'] = sub_name
                    dict['sub_category'].append(det['sub_category'])
            categoryList.append(dict)
        prod_list[0]["category"] = categoryList
        return JsonResponse({"code": 200, "status": "success","message": "successfully feteched", "details":prod_list})

            

class AddProducttoCart(APIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        serializer = SingleProductSerializer(data=request.data)
        if serializer.is_valid():
            product_id=serializer.data['product_id']
            if Cart.objects.filter(user_id=user_id).values('order_id').exists():
                order_id=Cart.objects.filter(user_id=user_id).values('order_id','products_id')
                for ord_id in order_id:
                    if Cart.objects.filter(user_id=user_id,products__products_id=product_id,is_taken=True).exists():
                        return Response({"code": 200, "status": "failure","message": "Already Added", "details": 'product already exist'})
                    saved=ProductInTransaction.objects.create(user_id=user_id,products_id=product_id,is_taken=True)
                    Cart.objects.create(user_id=user_id,products=saved,order_id=ord_id['order_id'],is_taken=True)
                    return Response({"code": 200, "status": "success","message": "Successfully Added", "details": serializer.data})
            elif Cart.objects.filter(user_id=user_id,products__products_id=product_id).exists():
                return Response({"code": 200, "status": "failure","message": "Already Added", "details": 'product already exist'})
            saved = ProductInTransaction.objects.create(user_id=user_id,products_id=product_id,quantity=1,is_taken=True)
            Cart.objects.create(user_id=user_id,products=saved,is_taken=True)
            return Response({"code": 200, "status": "success","message": "Successfully Added", "details": serializer.data})
        return JsonResponse({'message': "Unsuccessful", "status": "failure", 'code': '400', 'details': serializer.errors})


class CheckoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            token = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = token.user_id
        serializer = CheckoutSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.data
            datas = json.loads(data['products_id'])
            if ProductInTransaction.objects.filter(user_id=user_id,products_id=datas[0]['id']).exists():
                cart_item = Cart.objects.filter(user_id=user_id).values('products_id')
                for transaction_id in cart_item:
                    ProductInTransaction.objects.filter(user_id=user_id,products_id=datas[0]['id']).update(is_ordered=True)
                    data = Cart.objects.filter(user_id=user_id).values('order_id','is_ordered','products_id')
                    for i in data:
                        if i['order_id'] is None:
                            letters_and_digits = string.ascii_letters + string.digits
                            result_str = ''.join((random.choice(letters_and_digits) for i in range(6)))
                            ProductInTransaction.objects.filter(user_id=user_id,products_id=datas[0]['id']).update(is_ordered=True)
                            Cart.objects.filter(user_id=user_id).update(order_id=result_str,is_ordered=True)
                            return Response({"code": 200, "status": "success","message": "Successfully Checked","details":{"order_id":result_str}})
                        Cart.objects.filter(user_id=user_id).update(is_ordered=True)
                        ProductInTransaction.objects.filter(user_id=user_id,products_id=datas[0]['id']).update(is_ordered=True)
                        order_id = Cart.objects.filter(user_id=user_id).values('order_id')
                        for oid in order_id:
                            return Response({"code": 200, "status": "success","message": "Successfully Checked","details":oid})
            return Response({"code": 200, "status": "success","message": "Empty Cart","details":[]})
        return Response({'message': "Empty Fields", "status": "failure", 'code': '400', 'details': serializer.errors})


class AddProductCountAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})

        user_id = usid.user_id
        serializer = CartADDSerializer(data=request.data)
        if serializer.is_valid():
            if ProductInTransaction.objects.filter(user_id=user_id,products_id=serializer.data['products_id'],is_completed=False).exists():
                info = ProductInTransaction.objects.get(user=user_id,products_id=serializer.data['products_id'],is_completed=False)
                if info is not None:
                    info.quantity += 1
                    info.save()
                    Cart.objects.get_or_create(products=info,user_id=user_id)
                    information = CartADDSerializer(instance=info)
                    toret = []
                    total={}
                    total['grand_total']=[]
                    cart_details = ProductInTransaction.objects.filter(user=user_id,is_taken=True,is_completed=False).values(
                        'products', 'quantity', 'is_ordered','is_completed', 'is_taken', 'is_cancelled','created_at')
                    grand_total = 0
                    for cart_product in cart_details:
                        details = Product.objects.filter(id=cart_product['products'], deleted_at=None).values('id','photos','unit', 'likes', 'name', 'slug', 'description', 'discount_percent','product_address',
                                                    'summary', 'warning', 'visibility', 'quantity', 'old_price', 'price', 'categories', 'grand_total').distinct()
                        dict = {}
                        dict['id'] = cart_product['products']
                        dict['created_date'] = cart_product['created_at']

                        for price in details:
                            categories = Category.objects.filter(id=price['categories']).values('title','image')
                        for category in categories:
                            name = Category.objects.filter(id=price['categories']).values('id','title','image')
                            for one in name:
                                dict['category']=one['title']
                            dict['name']=price['name']
                            dict['product_discount']=str(price['discount_percent'])+'%'
                            dict['product_price'] = price['price']
                            dict['unit'] = price['unit']
                            dict['from'] = price['product_address']
                            dict['product_image']=[]
                            for image in details:
                                image1 = Photo.objects.filter(id=price['photos']).values('photo')
                                for img in image1:
                                    dict['image']='http://142.93.221.85/media/'+img['photo']
                                    dict['product_image'].append('http://142.93.221.85/media/'+img['photo'])

                            discount = str(price['discount_percent'])
                            dict['product_quantity'] = cart_product['quantity']
                            dict['is_ordered'] = cart_product['is_ordered']
                            dict['is_taken'] = cart_product['is_taken']
                            dict['is_cancelled'] = cart_product['is_cancelled']
                        if discount=='0.0':
                            dict['total_price']= price['price']*cart_product['quantity']
                            grand_total += dict['total_price']

                        else:
                            mp = price['price']
                            per_product_discount = (float(price['discount_percent']) / 100 ) * mp
                            sp = mp-per_product_discount
                            total_price = sp * cart_product['quantity']
                            dict['total_price'] = total_price
                            grand_total += dict['total_price']
                        toret.append(dict)
                    return Response({'code': 200, 'status': "SUCCESSFUL", 'message': "Successfully Updated Count",'details': toret,'grand_total':str(grand_total)})
                return Response({'code': 404, 'status': 'FAILURE', 'message': 'Cart Not Found'})
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Cart Not Found'})
        return JsonResponse({'message': "Unsuccessful", "status": "failure", 'code': '400', 'details': serializer.errors})


class  RemoveProductCountAPIView(APIView):

    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = usid.user_id
        serializer = CartADDSerializer(data=request.data)
        if serializer.is_valid():
            if ProductInTransaction.objects.filter(user_id=user_id,products_id=serializer.data['products_id'],is_completed=False).exists():
                info = ProductInTransaction.objects.get(user=user_id,products_id=serializer.data['products_id'],is_completed=False)
                if info is not None:
                    info.quantity -= 1
                    total={}
                    total['grand_total']=[]
                    grand_total=0
                    if info.quantity==0:
                        delt=ProductInTransaction.objects.get(user_id=user_id,products_id=serializer.data['products_id'],is_completed=False).delete()
                        Cart.objects.filter(products=delt).delete()
                        data= ProductInTransaction.objects.filter(user=user_id,products_id=serializer.data['products_id'],is_completed=False).delete()
                        toret = []
                        cart_details = ProductInTransaction.objects.filter(user=user_id,is_taken=True,is_completed=False).values('products', 'quantity', 'is_ordered','is_completed', 'is_taken', 'is_cancelled','created_at')
                        for cart_product in cart_details:
                            details = Product.objects.filter(id=cart_product['products'],deleted_at=None).values('id','photos','unit', 'likes', 'name', 'slug', 'description', 'discount_percent','product_address',
                                                    'summary', 'warning', 'visibility', 'quantity', 'old_price', 'price', 'categories')
                            dict = {}
                            dict['id'] = cart_product['products']
                            dict['created_date'] = cart_product['created_at']
                            for price in details:
                                categories = Category.objects.filter(id=price['categories']).values('title','image')
                                for category in categories:
                                    name = Category.objects.filter(id=price['categories']).values('id','title','image')
                                    for one in name:
                                        dict['category']=one['title']
                                dict['name']=price['name']
                                dict['product_discount']=str(price['discount_percent'])+'%'
                                dict['product_price'] = price['price']
                                dict['unit'] = price['unit']
                                dict['from'] = price['product_address']
                                dict['product_image']=[]
                                for image in details:
                                    image1 = Photo.objects.filter(id=price['photos']).values('photo')
                                    for img in image1:
                                        dict['image']='http://142.93.221.85/media/'+img['photo']
                                        dict['product_image'].append('http://142.93.221.85/media/'+img['photo'])

                            discount = str(price['discount_percent'])
                            dict['product_quantity'] = cart_product['quantity']
                            dict['is_ordered'] = cart_product['is_ordered']
                            dict['is_taken'] = cart_product['is_taken']
                            dict['is_cancelled'] = cart_product['is_cancelled']
                            if discount=='0.0':
                                dict['total_price']= price['price']*cart_product['quantity']
                                grand_total += dict['total_price']
                                dict['total_price']= price['price']*cart_product['quantity']
                            else:
                                mp = price['price']
                                per_product_discount = (float(price['discount_percent']) / 100 ) * mp
                                sp = mp-per_product_discount
                                total_price = sp * cart_product['quantity']
                                dict['total_price'] = total_price
                                grand_total += dict['total_price']
                            toret.append(dict)
                        return Response({'code': 200, 'status': "successful", 'message': "Successfully Deleted Cart",'details': toret,'grand_total':str(grand_total)})
                    info.save()
                    information = CartADDSerializer(instance=info)
                    toret = []
                    cart_details = ProductInTransaction.objects.filter(user=user_id,is_completed=False).values(
                        'products', 'quantity', 'is_ordered','is_completed', 'is_taken', 'is_cancelled','created_at')
                    for cart_product in cart_details:
                        details = Product.objects.filter(id=cart_product['products'],deleted_at=None).values('id','photos','unit', 'likes', 'name', 'slug', 'description', 'discount_percent','product_address',
                                                    'summary', 'warning', 'visibility', 'quantity', 'old_price', 'price', 'categories')
                        dict = {}
                        dict['id'] = cart_product['products']
                        dict['created_date'] = cart_product['created_at']
                        for price in details:
                            categories = Category.objects.filter(id=price['categories']).values('title','image')
                            for category in categories:
                                name = Category.objects.filter(id=price['categories']).values('id','title','image')
                                for one in name:
                                    dict['category']=one['title']
                            dict['name']=price['name']
                            dict['product_discount']=str(price['discount_percent'])+'%'
                            dict['product_price'] = price['price']
                            dict['unit'] = price['unit']
                            dict['from'] = price['product_address']
                            dict['product_image']=[]
                            for image in details:
                                image1 = Photo.objects.filter(id=price['photos']).values('photo')
                                for img in image1:
                                    dict['image']='http://142.93.221.85/media/'+img['photo']
                                    dict['product_image'].append('http://142.93.221.85/media/'+img['photo'])
                            discount = str(price['discount_percent'])
                            dict['product_quantity'] = cart_product['quantity']
                            dict['is_ordered'] = cart_product['is_ordered']
                            dict['is_taken'] = cart_product['is_taken']
                            dict['is_cancelled'] = cart_product['is_cancelled']
                        if discount=='0.0':
                            dict['total_price']= price['price']*cart_product['quantity']
                            grand_total += dict['total_price']
                        else:
                            mp = price['price']
                            per_product_discount = (float(price['discount_percent']) / 100 ) * mp
                            sp = mp-per_product_discount
                            total_price = sp * cart_product['quantity']
                            dict['total_price'] = total_price
                            grand_total += dict['total_price']
                        toret.append(dict)
                    return Response({'code': 200, 'status': "SUCCESSFUL", 'message': "Successfully Updated Count",'details': toret,'grand_total':str(grand_total)})
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Cart Not Found'})
        return JsonResponse({'message': "Unsuccessful", "status": "failure", 'code': '400', 'details': serializer.errors})


class ConfirmCheckoutAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = usid.user_id

        serializer = ConfirmCheckoutSerializer(data=request.data)
        if serializer.is_valid():
            toRet=[]
            dicti={}
            order_id=serializer.data['order_id']
            if Cart.objects.filter(user_id=user_id,order_id=order_id,is_completed=False).first():
                if serializer.data['gateway'] == "KHALTI":
                    quantity=ProductInTransaction.objects.filter(user_id=user_id).values('id','quantity','products_id')
                    for product_quantity in quantity:
                        in_stock=Product.objects.filter(id=product_quantity['products_id'],deleted_at=None).values('quantity')
                        for stock in in_stock:
                            product_stock = stock['quantity']
                            make_update = int(stock['quantity'])-int(product_quantity['quantity'])
                            Product.objects.filter(id=product_quantity['products_id'],deleted_at=None).update(quantity=make_update)
                            ProductInTransaction.objects.filter(user_id=user_id,products_id=product_quantity['products_id']).update(is_completed=True)
                            iid=Status.objects.get(name='Ordered').pk
                            Order.objects.create(user_id=user_id,products=product_quantity['id'],code=order_id,payment_type='Online Pay',condition_status_id=iid)
                            Cart.objects.filter(order_id=order_id).delete()
                    toRet.append(dicti)
                    return Response({'code': '200',"status": "success",'message': "Order Placed Successfully",  'details':toRet})
                elif serializer.data['gateway'] == "ESEWA":
                    dicti['order_id'] = order_id
                    dicti['merchant_id'] = "JB0BBQ4aD0UqIThFJwAKBgAXEUkEGQUBBAwdOgABHD4DChwUAB0R"
                    dicti['merchant_secret'] = "BhwIWQQADhIYSxILExMcAgFXFhcOBwAKBgAXEQ=="
                    dicti['scd'] = "epay_payment"
                    quantity=ProductInTransaction.objects.filter(user_id=user_id,is_ordered=True).values('quantity','products_id','id')
                    for product_quantity in quantity:
                        in_stock=Product.objects.filter(id=product_quantity['products_id'], deleted_at=None).values('quantity')
                        for stock in in_stock:
                            product_stock = stock['quantity']
                            make_update = int(stock['quantity'])-int(product_quantity['quantity'])
                            Product.objects.filter(id=product_quantity['products_id'], deleted_at=None).update(quantity=make_update)
                            ProductInTransaction.objects.filter(user_id=user_id,products_id=product_quantity['products_id']).update(is_completed=True)
                            avr=Order.objects.create(user_id=user_id,code=order_id,payment_type='Online Pay')
                            Cart.objects.filter(order_id=order_id).delete()
                    toRet.append(dicti)
                    return Response({'code': '200',"status": "success",'message': "Order Placed Successfully",  'details':toRet})
                elif serializer.data['gateway']== 'CASHONDELIVERY':
                    quantity=ProductInTransaction.objects.filter(user_id=user_id,is_completed=False).values('quantity','products_id','id')
                    iid=Status.objects.get(name='Ordered').pk
                    ord=Order(user_id=user_id,code=order_id,payment_type='Cash on Delivery',condition_status_id=iid)
                    ord.save()
                    for product_quantity in quantity:
                        in_stock=Product.objects.filter(id=product_quantity['products_id'], deleted_at=None).values('quantity')
                        for stock in in_stock:
                            product_stock = stock['quantity']
                            make_update = int(stock['quantity'])-int(product_quantity['quantity'])
                            Product.objects.filter(id=product_quantity['products_id'], deleted_at=None).update(quantity=make_update)
                            ProductInTransaction.objects.filter(user_id=user_id,products_id=product_quantity['products_id']).update(is_completed=True)
                            ord.products.add(product_quantity['id'])
                            Cart.objects.filter(order_id=order_id).delete()
                    toRet.append(dicti)
                    return Response({'code': '200',"status": "success",'message': "Order Placed Successfully"})
                return JsonResponse({'code': '400',"status": "failure",'message': "Unsuccessful", 'details': 'Not a valid payment method'})
            return JsonResponse({'code': '400',"status": "failure",'message': "Cart Doesnot Exist",  'details': []})
        return JsonResponse({'code': '400',"status": "failure",'message': "Unsuccessful", 'details': serializer.errors})


class GetPreviousOrderAPIView(APIView):
    def get(self, request, *args, **kwargs):
        global grand_total
        grand_total = 0
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'FAILURE', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'FAILURE', 'message': 'Invalid Credentials'})
        user_id = usid.user_id
        if Order.objects.filter(user_id=user_id).first():
            wrapper = []
            oid=Order.objects.filter(user_id=user_id).values('products','code','created_at','condition_status__name','payment_type')
            for order_id in oid:
                todict = {}
                todict['order_id'] = order_id['code']
                todict['created_date']=order_id['created_at']
                todict['estimated_date']='3 day'
                todict['payment_type']=order_id['payment_type']
                todict['conditional_status']=order_id['condition_status__name']
                todict['total']=0
                details = Order.objects.filter(user_id=user_id,code=order_id['code']).values('products')
                todict['items'] = []
                grand_total=0
                for i in details:
                    code = i['products']
                    dicti={}
                    productINT= ProductInTransaction.objects.filter(user_id=user_id,id=code,is_completed=True).values()
                    for j in productINT:
                        pid = j['products_id']
                        dict11 = Product.objects.filter(id=pid).values('id','photos','unit', 'likes', 'name', 'slug', 'description', 'discount_percent','product_address','summary', 'warning', 
                        'visibility', 'quantity', 'old_price', 'price', 'categories')
                        dicti['id'] = j['products_id']
                        dicti['created_date'] = j['created_at']
                        dicti['product_quantity']=j['quantity']
                        for price in dict11:
                            categories = Category.objects.filter(id=price['categories']).values('title','image')
                            dicti['category']= categories.first()['title']
                            for category in categories:
                                name = Category.objects.filter(id=price['categories']).values('id','title','image')
                        dicti['name']=price['name']
                        dicti['product_discount']=str(price['discount_percent'])+'%'
                        dicti['product_price'] = price['price']
                        dicti['unit'] = price['unit']
                        dicti['from'] = price['product_address']
                        dicti['product_image']=[]
                        for image in dict11:
                            image1 = Photo.objects.filter(id=image['photos']).values('photo')
                            for img in image1:
                                dicti['image']='http://142.93.221.85/media/'+img['photo']
                                dicti['product_image'].append('http://142.93.221.85/media/'+img['photo'])
                        discount = str(price['discount_percent'])
                        dicti['is_ordered'] = j['is_ordered']
                        dicti['is_taken'] = j['is_taken']
                        dicti['is_cancelled'] = j['is_cancelled']
                        if discount=='0.0':
                            dicti['total_price']= price['price']*j['quantity']
                            grand_total += dicti['total_price']
                        else:
                            total_price = price['price']*j['quantity']
                            discount = (total_price/100)*price['discount_percent']
                            price1 = total_price-discount
                            dicti['total_price'] = price1
                            grand_total += dicti['total_price']
                        todict['items'].append(dicti)
                todict['total']=grand_total
                if todict not in wrapper:
                    wrapper.append(todict)
            return Response({"code": 200, "status":"success", "message": "Successfully Feteched", "details": wrapper})
        return Response({"code": 200, "status": "success", "message": "Empty orders", "details": []})


class UpdateBillingAddressAPIView(APIView):
    serializer_class = UpdateAddressSerializer
    model = User

    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})
        user_id=usid.user_id
        serializer = UpdateBillingAddressSerializer(data=request.data)
        if serializer.is_valid():
            new_data = serializer.data
            try:
                if new_data['lat']:
                    try:
                        if new_data['postal_code']:
                            address = ShippingAddress.objects.filter(user_id=user_id,id=new_data['id']).update(
                                                    postal_code=new_data['postal_code'],city=new_data['city'],name=new_data['name'],country=new_data['country'],
                                                    lat=new_data['lat'],lng=new_data['lng'],contact_number=new_data['contact_number'],
                                                    street_name=new_data['street_name'])
                    except KeyError:
                        address = ShippingAddress.objects.filter(user_id=user_id,id=new_data['id']).update(
                                                    city=new_data['city'],name=new_data['name'],country=new_data['country'],
                                                    lat=new_data['lat'],lng=new_data['lng'],contact_number=new_data['contact_number'],
                                                    street_name=new_data['street_name'])
            except KeyError:
                try:
                    if new_data['postal_code']:
                        address = ShippingAddress.objects.filter(user_id=user_id,id=new_data['id']).update(
                                                postal_code=new_data['postal_code'],city=new_data['city'],name=new_data['name'],country=new_data['country'],
                                                street_name=new_data['street_name'],contact_number=new_data['contact_number'])
                except KeyError:
                    address = ShippingAddress.objects.filter(user_id=user_id,id=new_data['id']).update(
                                            city=new_data['city'],name=new_data['name'],country=new_data['country'],
                                            street_name=new_data['street_name'],contact_number=new_data['contact_number'])
            data = ShippingAddress.objects.filter(user_id=user_id).values()
            toret=[]
            for resp in data:
                dicti={}
                dicti['id']=resp['id']
                dicti['user_id']=resp['user_id']
                dicti['contact_number']=resp['contact_number']
                dicti['postal_code']=resp['postal_code']
                dicti['city']=resp['city']
                dicti['name']=resp['name']
                dicti['street_name']=resp['street_name']
                dicti['country']=resp['country']
                dicti['latitide']=resp['lat']
                dicti['longitude']=resp['lng']
            toret.append(dicti)
            return Response({"code": HTTP_200_OK, "status": "success", "message": "Updated Successfully", "details": toret})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Fields", "details": serializer.errors})


class CancelOrderAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})
        user_id=usid.user_id
        serializer = CancelSerializer(data=request.data)
        if serializer.is_valid():
            if Order.objects.filter(user_id=user_id,code=serializer.data['order_id']).first():
                iid=Status.objects.get(name='Cancelled').pk
                Order.objects.filter(user_id=user_id,code=serializer.data['order_id']).update(condition_status_id=iid)
                return Response({"code": HTTP_200_OK, "status": "success", "message": "Order Cancelled"})
            return Response({"code": HTTP_200_OK, "status": "success", "message": "Order Doesnot Exist"})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Field", "details": serializer.errors})


class OrderSummaryAPIView(APIView):

    def get(self, request, *args, **kwargs):
        try:
            token = request.META['HTTP_AUTHORIZATION']
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        try:
            token = (token.split("er")[1])
        except:
            return Response({'code': 400, 'status': 'failure', 'message': 'No Token Keyword Provided'})
        try:
            usid = Token.objects.get(key=token)
        except:
            return Response({'code': 404, 'status': 'failure', 'message': 'Invalid Credentials'})
        user_id=usid.user_id
        order_id = self.request.query_params.get('order_id')
        gateway = self.request.query_params.get('gateway')
        address_id = self.request.query_params.get('address_id')

        carts = Cart.objects.filter(user_id=user_id,order_id=order_id)
        items = []
        grand_total = 0
        dict = {}
        for cart in carts:
            pit = cart.products
            uri = 'http://142.93.221.85'
            prod = {}
            prod['id'] = pit.products.id
            prod['product_quantity'] = pit.quantity
            prod['name'] = pit.products.name
            prod['from'] = pit.products.product_address
            prod['unit'] = pit.products.unit
            prod['product_price'] = pit.products.price
            prod['total_price'] = pit.products.grand_total
            grand_total = grand_total + prod['total_price']
            prod['product_image'] = []
            prod['image'] = uri+pit.products.photos.all().first().photo.url
            for image in pit.products.photos.all():
                prod['product_image'].append(uri+image.photo.url)
            items.append(prod)
        dict['product'] = items
        dict['grand_total'] = str(grand_total)
        dict['address'] = {}
        shipping_address = ShippingAddress.objects.get(id=address_id)
        dict['address']['id'] = shipping_address.id 
        dict['address']['full_address'] = shipping_address.full_address()
        dict['payment_method'] = gateway
        final_list = []
        final_list.append(dict)
        return Response({"code": HTTP_200_OK, "status": 'success', "message": "Fetched Successfully", "details": final_list})


class GetSimilarProductsAPIView(APIView):
    def post(self, request):
        serializer = ProductIDSerializer(data=request.data)
        if serializer.id_valid():
            category_title = serializer.data['category_title']
            category = Category.objects.filter(title = category_title)
            queryset = Product.objects.filter(categories = category[0]).order_by('?')[:10]
            toret = []
            for details in queryset:
                dict = {}
                product_name = details.name
                product_price = details.price
                product_stock = details.quantity
                product_oldPrice = details.old_price
                product_category = details.categories
                product_address = details.product_address
                product_discount = details.discount_percent
                likes = details.likes
                dict['id'] = details.pk
                dict['name'] = product_name
                uri = 'http://142.93.221.85/media/'
                dict['product_image']=[]
                image = details.photos.all()
                for img in image:
                    dict['product_image'].append('http://142.93.221.85/media/'+str(img))
                dict['likes'] = likes
                dict['image']=uri+str(image[0])
                dict['quantity'] = product_stock
                dict['description'] = details.description
                dict['product_discount'] = str(product_discount)+''+'%'
                dict['old_price'] = product_oldPrice
                dict['from'] = product_address
                dict['product_price'] = product_price
                new_price = (product_price/100.0)*product_discount
                total_price = product_price-new_price
                dict['total_price'] = new_price
                toret.append(dict)
            return JsonResponse({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toret})
        return Response({"code": HTTP_400_BAD_REQUEST, "status": 'failure', "message": "Empty Fields", "details": serializer.errors})


class GetADSAPIView(APIView):
    def get(self,request):
        uri = socket.gethostbyname(socket.gethostname())
        ads = Advertisements.objects.all()
        toList = []
        for ads_data in ads:
            toret = {}
            toret['name'] = ads_data.name
            if ads_data.image:
                toret['image'] = uri + ads_data.image.url
            else:
                toret['image'] = ''
            if ads_data.logo:
                toret['logo'] = uri + ads_data.logo.url
            else:
                toret['logo'] = ''
            toret['image_url'] = ads_data.image_url
            toList.append(toret)
        return JsonResponse({"code": 200, "status": "success", "message": "Successfully Feteched", "details": toList})
