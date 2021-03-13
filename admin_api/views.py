from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse
from .serializers import *
from rest_framework.views import APIView
from cart.models import *
from account.models import *
import uuid
import socket
import datetime
from rest_framework.permissions import IsAuthenticated


class AddProductsAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        user_id = request.user.id
        serializer = AddProductsSerializers(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(id=user_id)
            if not user.is_staff:
                return JsonResponse({"code": 404, "status": 'failure', "message": "Access Denied", "details": {}})


            sub_categories = serializer.data['sub_categories']
            category_title = serializer.data['category_title']
            category_image = serializer.data['category_image']
            category_slug = serializer.data['category_slug']
            
            
            
            product_name = serializer.data['product_name']
            product_weight = serializer.data['product_weight']
            product_slug = serializer.data['product_slug']

            product_photos = request.data['image']

            description = serializer.data['description']
            summary = serializer.data['summary']
            warning = serializer.data['warning']
            quantity = serializer.data['quantity']
            owner = serializer.data['owner']
            tags = serializer.data['tags']
            unit = serializer.data['unit']
            price = serializer.data['price']
            discount_percent = serializer.data['discount_percent']
            child_category = SubCategory.objects.get_or_create(name = sub_categories)

            category = Category.objects.get_or_create(
                title = category_title, 
                slug = category_slug, 
            )
            print(category,' this is fuckin category')
            cat_group = SubCategoryMapping.objects.get_or_create(category_id = category[0].id, sub_category_id = child_category[0].id)

            try:
                category_description = serializer.data['category_description']
                category.save(category_description=category_description)
            except KeyError:
                pass
            product_slug = product_name.join('-')+ str(uuid.uuid4())
            products = Product.objects.create(
                name = product_name, 
                product_weight = product_weight, 
                price = price,
                description = description,
                summary = summary,
                warning = warning,
                quantity = quantity,
                owner = owner,
                unit = unit,
                slug=product_slug,
                discount_percent = discount_percent,
                )
            pic = Photo(photo=product_photos)
            pic.save()
            image = products.photos.add(pic)

            try:
                vat =  serializer.data['vat']
                products.save(vat=vat)
            except:
                pass
            
            try:
                seo_title = serializer.data['seo_title']
                products.save(seo_title=seo_title)
            except:
                pass
            try:
                seo_description = serializer.data['seo_description']
                products.save(seo_description=seo_description)
            except:
                pass
            try:
                seo_keywords = serializer.data['seo_keywords']
                products.save(seo_keywords=seo_keywords)
            except:
                pass
            try:
                vat_included = serializer.data['vat_included']
                products.save(vat_included=vat_included)
            except:
                pass
            try:
                vat_amount = serializer.data['vat_amount']
                products.save(vat_amount=vat_amount)
            except:pass
            try:
                expire_on = serializer.data['expire_on']
                products.save(expire_on=expire_on)
            except:pass
            try:
                is_new = serializer.data['is_new']
                products.save(is_new=is_new)
            except:
                pass
            try:
                is_on_sale = serializer.data['is_on_sale']
                products.save(is_on_sale=is_on_sale)
            except:pass
            try:
                is_coming_soon =  serializer.data['is_coming_soon']
                products.save(is_coming_soon=is_coming_soon)
            except:
                pass
            try:
                variant =  serializer.data['variant']
                products.save(variant=variant)
            except:
                pass
            try:
                priority = serializer.data['priority']
                products.save(priority=priority)
            except:pass
            try:
                product_address = serializer.data['product_address']
                products.save(product_address=product_address)
            except:pass
            return JsonResponse({"code": 200, "status": 'success', "message": "Product Added", "details": serializer.data})
        return JsonResponse({"code": 400, "status": 'failure', "message": "Empty Field", "details": serializer.errors})



class GetProductAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    uri = 'http://'+socket.gethostbyname(socket.gethostname())+'/media/'
    def get(self, request):
        user_id = request.user.id
        toList = []
        user = User.objects.filter(id=user_id)
        if user[0].is_staff:
            product_data = Product.objects.filter(
                deleted_at = None
                )
            for data in product_data:
                toret = {}
                toret['id'] = data.id
                toret['name'] = data.name
                toret['product_weight'] = data.product_weight
                toret['slug'] = data.slug
                toret['product_image'] = []
                images = Photo.objects.filter(product=data.id)
                for image in images:
                    toret['image'] = self.uri+image.photo.url
                    toret['product_image'].append(self.uri+image.photo.url)
                toret['description'] = data.description
                toret['summary'] = data.summary
                toret['warning'] = data.warning
                toret['visibility'] = data.visibility
                toret['reference_code'] = data.reference_code
                toret['barcode'] = data.barcode
                toret['quantity'] = data.quantity
                toret['category'] = []
                categories = Category.objects.filter(product=data.id)
                for cat in categories:
                    toret['category'].append(cat.title)
                toret['owner'] = data.owner
                toret['tags'] = []
                tags = Tag.objects.filter(product=data.id)
                for tag in tags:
                    toret['tags'].append(tag.title)
                toret['unit'] = data.unit
                toret['old_price'] = data.old_price
                toret['price'] = data.price
                toret['vat'] = data.vat
                toret['vat_included'] = data.vat_included
                toret['vat_amount'] = data.vat_amount
                toret['discount_percent'] = data.discount_percent
                toret['is_new'] = data.is_new
                toret['is_on_sale'] = data.is_on_sale
                toret['is_coming_soon'] = data.is_coming_soon
                toret['order_count'] = data.order_count
                toret['likes'] = data.likes
                toret['priority'] = data.priority
                toret['product_address'] = data.product_address
                toList.append(toret)
            return JsonResponse({"code": 200, "status": 'success', "message": "Feteched Successfully", "details": toList})   
        return JsonResponse({"code": 400, "status": 'unauthorized', "failure": "unauthorized access", "details": []})


class DeleteProductAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request):
        user_id = request.user.id
        toList = []
        user = User.objects.filter(id=user_id)
        if user[0].is_staff:
            serializer = ProductIDSerializer(
                data=request.data
                )
            if serializer.is_valid():
                product_id = serializer.data['product_id']
                Product.objects.filter(
                    id=product_id
                    ).update(
                        deleted_at = datetime.datetime.now()
                    )
                return JsonResponse({
                    "code": 200, 
                    "status": 'success',
                    "message": "Deleted Successfully",
                    "details": []
                    })   
            return JsonResponse({
                "code": 400,
                "status":"failure",
                'message':"Empty Field",
                "details": serializer.errors
                })
        return JsonResponse({
            "code": 401,
            "status": 'failure',
            'message':'unauthorized access',
            "details": []
            })


class GetOrderListAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user_id = request.user.id
        toList = []
        user = User.objects.filter(id=user_id)
        if user[0].is_staff==True:
            get_orders = Order.objects.filter(is_confirmed=False)
            toList = []
            for order in get_orders:
                toret = {}
                toret['customer_name'] = order.user.get_full_name()
                product_name = order.products.all()
                print(product_name,'product name')
                if not product_name:
                    return JsonResponse({
                        "code": 200,
                        "status":"failure",
                        'message':"Empty Data",
                        "details": []
                        })
                for product in product_name:
                    shipping_details = ShippingAddress.objects.filter(user_id=product.user.id)
                    for address in shipping_details:
                        toret['contact_number'] = address.contact_number
                        toret['city'] = address.city
                        toret['postal_code'] = address.postal_code
                        toret['street_name'] = address.street_name
                        toret['lat'] = address.lat
                        toret['lng'] = address.lng
                    product_price = product.products.price
                    toret['product_name'] = product.products.name
                    toret['product_price'] = product_price
                    discount_percent = product.products.discount_percent
                    toret['product_discount'] = str(discount_percent)+'%'
                    quantity = product.quantity
                    toret['product_quantity'] = quantity
                    if discount_percent==0:
                            toret['with_discount']= product_price*quantity
                    else:
                        total_price = product_price*quantity
                        discount = (total_price/100)*discount_percent
                        price1 = total_price-discount
                        toret['with_discount'] = price1
                toList.append(toret)
            return JsonResponse({
            "code": 401,
            "status": 'failure',
            'message':'unauthorized access',
            "details": toList
            })
        return JsonResponse({
            "code": 401,
            "status": 'failure',
            'message':'unauthorized access',
            "details": []
            })