from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse
from .serializers import *
from rest_framework.views import APIView
from cart.models import *
from account.models import *
from rest_framework.authtoken.models import Token
import uuid
# Create your views here.


def CheckHttpAuthorization(auth_token):
    token = auth_token
    if not auth_token:
        return JsonResponse({'code': 400, 'status': 'FAILURE', 'message': 'user not provided'})

    try:
        token = (token.split("arer ")[1])
        try:
            usid = Token.objects.get(key=token)
        except Token.DoesNotExist:
            return JsonResponse({'code': 404, 'status': 'FAILURE', 'message': 'provided credentials not found'})
    except:
        return JsonResponse({'code': 400, 'status': 'FAILURE', 'message': 'no token keyword provided'})

    user_id = usid.user_id
    return user_id



class AddProductsAPIView(APIView):
    def post(self, request):
        
        try:
            uid = CheckHttpAuthorization(auth_token=request.META['HTTP_AUTHORIZATION'])
        except KeyError:
            return JsonResponse({'code': 400, 'status': 'failure', 'message': 'User Token Not Provided'})
        if uid.__class__.__name__ == 'JsonResponse':
            return uid
        else:
            user_id = uid

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
            print(type(child_category[0]),' this is fuckin child_category')

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
            print(product_photos,' image from serializer')
            print(products.photos)
            pic = Photo(photo=product_photos)
            pic.save()
            image = products.photos.add(pic)
            print(image,'image')

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
