import random
import string
import datetime
import json
import csv, subprocess
import requests

from xhtml2pdf import pisa
from io import StringIO, BytesIO
from django.template import Context
from django.template.loader import get_template

from django.apps import apps
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.shortcuts import redirect, get_object_or_404
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import (
    CreateView, ListView, UpdateView, FormView, View, DeleteView, DetailView,
    TemplateView)
from django.contrib.auth.models import Group
from django.utils.text import slugify
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.utils.html import strip_spaces_between_tags, strip_tags
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.shortcuts import render
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.db.models import Sum



from notifications.models import Notification
from notifications.signals import notify

from dal import autocomplete

from .models import *
from .forms import *
from .create_label import barcode_generator, image_save
from account.models import Subscriber
from account.models import User as CustomUser
# from messaging.models import *


class BaseMixin(object):
    def get_context_data(self, **kwargs):
        context = super(BaseMixin,self).get_context_data(**kwargs)
        # context['message_count'] = Message.objects.filter(deleted_at=None, is_read=False).count()
        context['orders_count'] = Order.objects.filter(deleted_at=None).count()
        context['categories'] = Category.objects.filter(deleted_at=None).exclude(slug='root')[:5]
        context['clients'] = User.objects.filter(customer_type='Registered')
        sales = Sales.objects.filter(deleted_at__isnull=True).aggregate(Sum('order__total'))
        context['sales'] = sales['order__total__sum']
        return context


class DashBoard(BaseMixin, TemplateView):
    template_name = 'dashboard.html'


class MarkAllRead(BaseMixin, View):

    def dispatch(self, request, *args, **kwargs):
        request.user.notifications.mark_all_as_read()
        return redirect('/gaava-admin/')


class MarkAsRead(BaseMixin,View):

    def dispatch(self, request, *args, **kwargs):
        id = self.kwargs['pk']
        notification = get_object_or_404(
            Notification, recipient=request.user, id=id)
        notification.unread = False
        notification.save()
        return redirect('/gaava-admin/')


# Git pull view
class GitPullView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        process = subprocess.Popen(['./pull.sh'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        returncode = process.wait()
        output = ''
        output += process.stdout.read().decode("utf-8")
        output += '\nReturned with status {0}'.format(returncode)
        response = HttpResponse(output)
        response['Content-Type'] = 'text'
        return response


class DeleteMixin(LoginRequiredMixin, BaseMixin, UpdateView):
    login_url = "/accounts/adminlogin/"

    def form_valid(self, form):
        form.instance.deleted_at = timezone.now()
        form.save()
        return super().form_valid(form)


class MultipleOptionConfirmation(TemplateView, BaseMixin):
    template_name = 'cart/multiple_options_confirmation.html'

    def dispatch(self, request, *args, **kwargs):
        model = self.kwargs['model']
        self.option = self.kwargs['option']
        self.id_list = self.request.POST.getlist('id_list')
        self.url = self.request.POST.get('urls')
        self.model = apps.get_model(app_label='cart', model_name=model)
        return super(MultipleOptionConfirmation, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if int(self.option) == 1:
            for ind in self.id_list:
                obj = self.model.objects.get(id=ind)
                obj.delete()
            messages.success(request, "Selected Items deleted successfully")
        elif int(self.option) == 2:
            for ind in self.id_list:
                obj = self.model.objects.get(id=ind) 
                if obj.visibility == False:
                    obj.visibility = True
                obj.save()
            messages.success(request, "Selected Items Made Visible successfully")
        elif int(self.option) == 3:
            for ind in self.id_list:
                obj = self.model.objects.get(id=ind) 
                if obj.is_new == False:
                    obj.is_new = True
                obj.save()
            messages.success(request, "Selected Items Marked as New successfully")
        elif int(self.option) == 4:
            for ind in self.id_list:
                obj = self.model.objects.get(id=ind) 
                if obj.is_on_sale == False:
                    obj.is_on_sale = True
                obj.save()
            messages.success(request, "Selected Items Marked as Product on Sale successfully")
        elif int(self.option) == 5:
            for ind in self.id_list:
                obj = self.model.objects.get(id=ind) 
                if obj.is_coming_soon == False:
                    obj.is_coming_soon = True
                obj.save()
            messages.success(request, "Selected Items Marked as Coming Soon successfully")
        else:
            return reverse_lazy('cart:products')
        return HttpResponseRedirect(self.url)



class CreateTagView(LoginRequiredMixin, BaseMixin, View):

    def post(self, request, *args, **kwargs):
        print('here')
        form = TagAutoForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return JsonResponse({'id': obj.id }, status=200)
        else:
            pass


class CouponCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/coupon_form.html'
    model = Coupon
    form_class = CouponForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:coupons")
    success_message = "Coupon Successfully Added"

    def form_valid(self, form, **kwargs):
        couponObjects = Coupon.objects.filter(code=form.instance.code)
        if couponObjects:
            messages.error(self.request, "Coupon Code Already Exist!!!")
            return redirect('cart:coupon_create')
        else:
            form.save()
        return super().form_valid(form, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'coupon'
        return context


class CouponUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/coupon_form.html'
    model = Coupon
    form_class = CouponForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:coupons")
    success_message = "Coupon Successfully Updated"

    def form_valid(self, form, **kwargs):
        couponObjects = Coupon.objects.filter(code=form.instance.code).exclude(
            code=self.get_object().code)
        if not couponObjects:
            form.save()
        else:
            messages.error(self.request, "Coupon Code Already Exist!!!")
            return redirect('cart:coupons')
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'coupon'
        return context


class CouponListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/coupons.html'
    model = Coupon
    login_url = "/accounts/adminlogin/"
    queryset = Coupon.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'coupon'
        context['quick_form'] = QuickActionForm
        return context


class CouponDelete(SuccessMessageMixin, DeleteMixin):
    template_name = 'cart/delete_coupon.html'
    model = Coupon
    form_class = CouponDeleteForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:coupons")
    success_message = "Coupon deleted successfully"


class MultipleCouponDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:coupons")
        url_list = reverse_lazy("cart:coupons")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/coupons')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'coupon', 'option': option, 'ids': id_list,'urls':url })


class CategoryCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/category_form.html'
    model = Category
    form_class = CategoryForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:categories")
    success_message = "Category Successfully Added"

    def form_valid(self, form, **kwargs):
        categoryObjects = Category.objects.filter(slug=form.instance.title)
        if not categoryObjects:
            categoryobj = Category.objects.create(title=form.cleaned_data.get('title'),
            description=self.request.POST.get('description'),
            slug=slugify(form.instance.title), seo_title=form.cleaned_data['seo_title'],
            seo_description=form.cleaned_data['seo_description'])
            for keywords in form.data.getlist('seo_keywords'):
                kobj = Keywords.objects.get(id=keywords)
                categoryobj.seo_keywords.add(kobj)
                categoryobj.save()
        else:
            messages.error(self.request, "Category Already Exist!!!")
            return redirect('cart:category_create')

        return HttpResponseRedirect('/shop/categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'category'
        context['categories'] = Category.objects.filter(deleted_at=None)
        return context


class CategoryUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/category_form.html'
    model = Category
    form_class = CategoryForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:categories")
    success_message = "Category Successfully Updated"

    def form_valid(self, form, **kwargs):
        self.category = get_object_or_404(
            Category, pk=self.kwargs['pk'])
        categoryObjects = Category.objects.filter(slug=form.instance.title).exclude(slug=self.get_object().slug)
        if not categoryObjects:
            form.instance.slug = slugify(form.instance.title)
            form.save()
            self.category.seo_title = self.request.POST.get('seo_title')
            self.category.seo_description = self.request.POST.get('seo_description')
            self.category.save()
            self.category.seo_keywords.clear()
            for keyword in form.data.getlist('seo_keywords'):
                obj = Keywords.objects.get(id=keyword)
                self.category.seo_keywords.add(obj)
            self.category.save()
        else:
            messages.error(self.request, "Category Already Exist!!!")
            return redirect('cart:category_create')

        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'category'
        context['categories'] = Category.objects.filter(deleted_at=None)
        return context


class CategoryListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/categories.html'
    login_url = "/accounts/adminlogin/"
    queryset = Category.objects.filter(deleted_at__isnull=True).exclude(slug='root')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'category'
        context['quick_form'] = QuickActionForm
        context['category_delete_form'] = CategoryDeleteForm
        return context


class CategoryDelete(SuccessMessageMixin, DeleteMixin):
    model = Category
    form_class = CategoryDeleteForm
    success_url = reverse_lazy("cart:categories")
    success_message = "Category deleted successfully"


class MultipleCategoryDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:categories")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/categories')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'category', 'option': option, 'ids': id_list,'urls':url })


class ProductCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, FormView):
    template_name = 'cart/product_create.html'
    form_class = ProductForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:products")
    photo_form = ProductPhotoForm

    def form_valid(self, form):
        vat_amt = 0
        discount_amt = 0
        productObjects = Product.objects.filter(name=self.request.POST.get('name'))
        # if not productObjects:
        if self.request.POST.get('visibility') == 'on':
            visibility = True
        else:
            visibility = False
        if self.request.POST.get('vat_included') == 'on':
            vat_included = True
        else:
            vat_included = False
        slug =form.cleaned_data.get('name').lower().replace(" ", "-")
        if (Product.objects.filter(slug=slug)):
            slug = get_random_string(length=8)
        product_obj = Product.objects.create(
            name=form.cleaned_data.get('name'), reference_code=self.request.POST.get('reference_code'),
            barcode=self.request.POST.get('barcode'), visibility=visibility,
            description=self.request.POST.get('description'), summary=self.request.POST.get('summary'),
            quantity=self.request.POST.get('quantity'), price=form.cleaned_data.get('price'),
            old_price=form.cleaned_data.get('old_price'), owner=form.cleaned_data.get('owner'),
            product_address=form.cleaned_data.get('product_address'),unit=form.cleaned_data.get('unit'),
            vat=form.cleaned_data.get('vat'), discount_percent=form.cleaned_data.get('discount_percent'),
            vat_included=vat_included,expire_on=form.cleaned_data.get('expire_on'),
            warning=self.request.POST.get('warning'), slug=slug)
        for tag in form.cleaned_data['tags']:
            product_obj.tags.add(tag)
        for afile in self.request.FILES.getlist('photo'):
            pic = Photo()
            pic.photo = afile
            pic.title = self.request.POST.get('name')
            pic.save()
            product_obj.photos.add(pic)
        for cat in self.request.POST.getlist('categories'):
            cobj = Category.objects.get(id=cat)
            product_obj.categories.add(cobj)
        for prod in self.request.POST.getlist('variant'):
            obj = Product.objects.get(id=prod)
            product_obj.variant.add(obj)
        if self.request.POST.get('discount_percent'):
            discount_amt = ((float(self.request.POST.get('price')))*float(self.request.POST.get('discount_percent')))/100
            product_obj.discount_amount = str(discount_amt)
            product_obj.save()
        if vat_included:
            vat_amt = ((float(self.request.POST.get('price'))-float(discount_amt))*(float(self.request.POST.get('vat'))/100))
            product_obj.vat_amount = str(vat_amt)
            product_obj.save()
        if float(self.request.POST.get('discount_percent')) > 0:
            product_obj.is_on_sale = True
            product_obj.save()
        product_obj.grand_total = str(float(self.request.POST.get('price')) - discount_amt + vat_amt)
        product_obj.save()
        messages.success(self.request, "Product Created Successfully")
        if '_save' in self.request.POST:
            return redirect('cart:product_update', pk=product_obj.pk)
        else:
            return HttpResponseRedirect(reverse_lazy("cart:products"))


    def form_invalid(self, form):
        print(form.errors,3908123982323)
        return super().form_invalid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['photo_form'] = ProductPhotoForm
        context['url_name'] = 'product'

        return context


class ProductListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/products.html'
    model = Product
    login_url = "/accounts/adminlogin/"
    context_object_name = 'products'
    queryset = Product.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'product'
        context['quick_form'] = QuickProductActionForm
        option = self.request.GET.get('options')
        if option:
            context['opt'] = int(option)
        return context



class ExportProductCSV(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Reference Code', 'Quantity', 'Grand Total'])
        products = Product.objects.filter(deleted_at__isnull=True)
        for product in products:
            writer.writerow([
                product.name, product.reference_code, product.quantity, product.grand_total])
        return response


class ProductUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/product_create.html'
    form_class = ProductForm
    photo_form = ProductPhotoForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:products")
    success_message = "Product Successfully Updated"
    queryset = Product.objects.filter(deleted_at__isnull=True)

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(
            Product, pk=self.kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self, **kwargs):
        kw = super().get_form_kwargs(**kwargs)
        tags = self.product.tags.all()
        kw['initial'].update({
            'name': self.product.name,
            'reference_code': self.product.reference_code,
            'barcode': self.product.barcode,
            'visibility': self.product.visibility,
            'description': self.product.description,
            'summary': self.product.summary,
            'quantity': self.product.quantity,
            'categories': self.product.categories.all(),
            'variant': self.product.variant.all(),
            'tags': tags,
            'price': self.product.price,
            'vat': self.product.vat,
            'owner': self.product.owner,
            'product_address': self.product.product_address,
            'unit': self.product.unit,
            'vat_included': self.product.vat_included,
            'discount_percent': self.product.discount_percent,
            'discount_amount': self.product.discount_amount,
            'is_new': self.product.is_new,
            'is_on_sale': self.product.is_on_sale,
            'old_price': self.product.old_price,
            'is_coming_soon': self.product.is_coming_soon,
            'expire_on': self.product.expire_on,
            'priority': self.product.priority,
            'seo_title': self.product.get_seo_title,
            'seo_description': strip_tags(self.product.get_seo_description),
            # 'seo_keywords': self.product.get_seo_keywords,
        })
        if not self.product.seo_keywords.exists():
            for obj in tags:
                keyword, created = Keywords.objects.get_or_create(title=obj.title)
                self.product.seo_keywords.add(keyword)

        kw['initial']['seo_keywords'] = self.product.get_seo_keywords
        return kw

    def form_valid(self, form):
        vat_amt = 0
        discount_amt = 0
        old_qty = self.product.quantity
        tags_array = []
        tags_added = self.product.tags.all()
        for tag in self.request.POST.getlist('tags'):
            if tag.isdigit():
                try:
                    tag_obj = Tag.objects.get(id=tag)
                except Tag.DoesNotExist:
                    pass
            else:
                try:
                    tag_obj = Tag.objects.get(title=tag)
                except Tag.DoesNotExist:
                    tag_obj = Tag.objects.create(title=tag)
            tags_array.append(str(tag_obj.id))
                

        if self.request.POST.get('visibility') == 'on':
            visibility = True
        else:
            visibility = False
        if self.request.POST.get('is_new') == 'on':
            is_new = True
        else:
            is_new = False
        if self.request.POST.get('is_on_sale') == 'on':
            is_on_sale = True
        else:
            is_on_sale = False
        if self.request.POST.get('is_coming_soon') == 'on':
            is_coming_soon = True
        else:
            is_coming_soon = False
        if self.request.POST.get('vat_included') == 'on':
            vat_included = True
        else:
            vat_included = False
        self.product.name = self.request.POST.get('name')
        # self.product.slug = slugify(self.request.POST.get('name'))
        self.product.reference_code = self.request.POST.get('reference_code')
        self.product.barcode = self.request.POST.get('barcode')
        self.product.visibility = visibility
        self.product.description = self.request.POST.get('description')
        self.product.summary = self.request.POST.get('summary')
        self.product.seo_title = self.request.POST.get('seo_title')
        self.product.seo_description = self.request.POST.get('seo_description')
        self.product.quantity = self.request.POST.get('quantity')
        self.product.price = self.request.POST.get('price')
        self.product.vat = self.request.POST.get('vat')
        self.product.owner = self.request.POST.get('owner')
        self.product.product_address = self.request.POST.get('product_address')
        self.product.unit = self.request.POST.get('unit')
        self.product.vat_included = vat_included
        self.product.discount_percent = self.request.POST.get('discount_percent')
        self.product.is_new = is_new
        self.product.is_on_sale = is_on_sale
        if self.request.POST.get('old_price'):
            self.product.old_price = self.request.POST.get('old_price')
        else:
            pass
        self.product.is_coming_soon = is_coming_soon
        if self.request.POST.get('expire_on'):
            self.product.expire_on = self.request.POST.get('expire_on')
        else:
            pass
        self.product.priority = 0
        self.product.save()
        

        if int(self.product.quantity) > int(old_qty):
            notify_to = NotifyMe.objects.filter(
                deleted_at__isnull=True, product=self.product, is_emailed=False)
            from_email = settings.EMAIL_HOST_USER
            holders_email = []
            for holder in notify_to:
                holder.is_emailed = True
                holder.save()
                holders_email.append(holder.email)
            msg = 'Product named ' + self.product.name + ' is available now. Please proceed to checkout.'
            send_mail('Stock Available', msg, from_email, holders_email)

        self.product.categories.clear()
        for cat in self.request.POST.getlist('categories'):
            category = Category.objects.get(id=cat)
            self.product.categories.add(category)


        self.product.variant.clear()
        for prod in self.request.POST.getlist('variant'):
            obj = Product.objects.get(id=prod)
            self.product.variant.add(obj)

        self.product.tags.clear()
        for tag in tags_array:
            if tags_added.count() == 0:
                tag_id = Tag.objects.get(id=tag)
                self.product.tags.add(tag_id)
            else:
                for prod_tag in self.product.tags.all():
                    if not tag is prod_tag.id:    
                        tag_id = Tag.objects.get(id=tag)
                        self.product.tags.add(tag_id)

        self.product.seo_keywords.clear()
        for keyword in form.data.getlist('seo_keywords'):
            obj = Keywords.objects.get(id=keyword)
            self.product.seo_keywords.add(obj)

        for afile in self.request.FILES.getlist('photo'):
            pic = Photo()
            pic.photo = afile
            pic.title = form.instance.name
            pic.save()
            self.product.photos.add(pic)
        if vat_included:
            vat_amt = (float(self.request.POST.get('price'))*float(self.request.POST.get('vat')))/100
            self.product.vat_amount = str(vat_amt)
            self.product.save()
        if self.request.POST.get('discount_percent'):
            discount_amt = ((
                vat_amt + float(self.request.POST.get('price')))*float(self.request.POST.get('discount_percent')))/100
            self.product.discount_amount = str(discount_amt)
            self.product.save()
        if float(self.request.POST.get('discount_percent')) > 0:
            self.product.is_on_sale = True
            self.product.save()
        self.product.grand_total = str(float(self.request.POST.get('price')) + vat_amt - discount_amt)
        self.product.save()
        messages.success(self.request, "Products Updated Successfully")
        return HttpResponseRedirect(reverse("cart:products"))


    def form_invalid(self, form):
        return super().form_invalid(form)

    # def post(self, request, *args, **kwargs):
    #     if request.method == 'POST':
    #         form = ProductForm(request.POST)
    #         vat_amt = 0
    #         discount_amt = 0
    #         old_qty = self.product.quantity
    #         tags_array = []
    #         tags_added = self.product.tags.all()
    #         for tag in request.POST.getlist('tags'):
    #             if tag.isdigit():
    #                 try:
    #                     tag_obj = Tag.objects.get(id=tag)
    #                 except Tag.DoesNotExist:
    #                     pass
    #             else:
    #                 try:
    #                     tag_obj = Tag.objects.get(title=tag)
    #                 except Tag.DoesNotExist:
    #                     tag_obj = Tag.objects.create(title=tag)
    #             tags_array.append(str(tag_obj.id))
                    
    #         productObjects = Product.objects.filter(slug=form.instance.name).exclude(slug=self.product.slug)
    #         if not productObjects:
    #             if request.POST.get('visibility') == 'on':
    #                 visibility = True
    #             else:
    #                 visibility = False
    #             if request.POST.get('is_new') == 'on':
    #                 is_new = True
    #             else:
    #                 is_new = False
    #             if request.POST.get('is_on_sale') == 'on':
    #                 is_on_sale = True
    #             else:
    #                 is_on_sale = False
    #             if request.POST.get('is_coming_soon') == 'on':
    #                 is_coming_soon = True
    #             else:
    #                 is_coming_soon = False
    #             if request.POST.get('vat_included') == 'on':
    #                 vat_included = True
    #             else:
    #                 vat_included = False
    #             self.product.name = request.POST.get('name')
    #             # self.product.slug = slugify(request.POST.get('name'))
    #             self.product.reference_code = request.POST.get('reference_code')
    #             self.product.barcode = request.POST.get('barcode')
    #             self.product.visibility = visibility
    #             self.product.description = request.POST.get('description')
    #             self.product.summary = request.POST.get('summary')
    #             self.product.quantity = request.POST.get('quantity')
    #             self.product.price = request.POST.get('price')
    #             self.product.vat = request.POST.get('vat')
    #             self.product.vat_included = vat_included
    #             self.product.discount_percent = request.POST.get('discount_percent')
    #             self.product.is_new = is_new
    #             self.product.is_on_sale = is_on_sale
    #             self.product.old_price = request.POST.get('old_price')
    #             self.product.is_coming_soon = is_coming_soon
    #             # self.product.expire_on = request.POST.get('expire_on')
    #             self.product.save()

    #             if int(self.product.quantity) > old_qty:
    #                 notify_to = NotifyMe.objects.filter(
    #                     deleted_at__isnull=True, product=self.product, is_emailed=False)
    #                 from_email = settings.EMAIL_HOST_USER
    #                 holders_email = []
    #                 for holder in notify_to:
    #                     holder.is_emailed = True
    #                     holder.save()
    #                     holders_email.append(holder.email)
    #                 msg = 'Product named ' + self.product.name + ' is available now. Please proceed to checkout.'
    #                 send_mail('Stock Available', msg, from_email, holders_email)

    #             for cat in request.POST.getlist('categories'):
    #                 if self.product.categories.all():
    #                     for prod in self.product.categories.all():
    #                         if not cat is prod.id:
    #                             category = Category.objects.get(id=cat)
    #                             self.product.categories.add(category)
    #                 else:
    #                     category = Category.objects.get(id=cat)
    #                     self.product.categories.add(category) 

    #             for prod in request.POST.getlist('variant'):
    #                 obj = Product.objects.get(id=prod)
    #                 self.product.variant.add(obj)

    #             for tag in tags_array:
    #                 if tags_added.count() == 0:
    #                     tag_id = Tag.objects.get(id=tag)
    #                     self.product.tags.add(tag_id)
    #                 else:
    #                     for prod_tag in self.product.tags.all():
    #                         if not tag is prod_tag.id:    
    #                             tag_id = Tag.objects.get(id=tag)
    #                             self.product.tags.add(tag_id)

    #             for afile in request.FILES.getlist('photo'):
    #                 pic = Photo()
    #                 pic.photo = afile
    #                 pic.title = form.instance.name
    #                 pic.save()
    #                 self.product.photos.add(pic)
    #             if vat_included:
    #                 vat_amt = (float(request.POST.get('price'))*float(request.POST.get('vat')))/100
    #                 self.product.vat_amount = str(vat_amt)
    #                 self.product.save()
    #             if request.POST.get('discount_percent'):
    #                 discount_amt = ((
    #                     vat_amt + float(request.POST.get('price')))*float(request.POST.get('discount_percent')))/100
    #                 self.product.discount_amount = str(discount_amt)
    #                 self.product.save()
    #             if float(request.POST.get('discount_percent')) > 0:
    #                 self.product.is_on_sale = True
    #                 self.product.old_price = self.product.price
    #                 self.product.save()
    #             self.product.grand_total = str(float(request.POST.get('price')) + )
    #             self.product.save()
    #         else:
    #             messages.error(request, "Product Already Exist!!!")
    #             return redirect('cart:adminProductCreate')
    #         return HttpResponseRedirect(reverse("cart:products"))
    #         messages.error(request, "Form is not valid")
    #         return HttpResponseRedirect(reverse("cart:products"))
    #     return HttpResponseRedirect(reverse("cart:products"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo_form = ProductPhotoForm()
        print(photo_form)
        photo_form = ProductPhotoForm(instance=self.product)
        print(photo_form)
        photo_form = ProductPhotoForm(instance=self.get_object())
        print(photo_form)
        context['photo_form'] = photo_form
        context['product'] = self.product
        context['url_name'] = 'product'
        return context


class ProductDelete(SuccessMessageMixin, DeleteMixin):
    template_name = 'cart/delete_product.html'
    model = Product
    form_class = ProductDeleteForm
    success_url = reverse_lazy("cart:products")
    success_message = "Product deleted successfully"


class ProductPreview(LoginRequiredMixin, BaseMixin, DetailView):
    template_name = 'cart/product_preview.html'
    model = Product


class ProductDetails(View):
    def get(self, request, *args, **kwargs):
        print(request.GET['data'])
        prod_id= json.loads(request.GET['data'])
        product = Product.objects.get(id=prod_id)
        x = render_to_string('cart/product_details.html',
                {'product': product})
        return HttpResponse(x)


class OrderSearchView(View):
    def get(self, request, *args, **kwargs):
        print(request.GET['data'])
        prod_id= json.loads(request.GET['data'])
        product = Product.objects.get(id=prod_id)
        x = render_to_string('cart/product_details.html',
                {'product': product})
        return HttpResponse(x)


class MultipleProductDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:products")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/products')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'product', 'option': option, 'ids': id_list,'urls':url})



def export_product_detail(request, **kwargs):
    template = get_template("cart/product_pdf.html")
    product_id = kwargs['product_id']
    product = Product.objects.get(id=product_id)
    html = template.render({'product': product})
    Context({'pagesize':'A4'}) 
    result = BytesIO() 
    pdf = pisa.CreatePDF(StringIO(html), result) 
    if not pdf.err: 
        return HttpResponse(result.getvalue(), content_type='application/pdf') 
    else: 
        return HttpResponse('Errors')
    return response


class ExportProductCSV(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="product_list.csv"'
        writer = csv.writer(response)
        writer.writerow(['Product ID', 'Name', 'Categories', 'Price tax excluded', 'On sale', 'Discount amount', 'Discount percent', 'Quantity', 'Summary', 'Description', 'Tags', 'Image url','Reference code'])
        products = Product.objects.filter(deleted_at__isnull=True)
        for product in products: 
            writer.writerow([
                product.id, product.name, ','.join([str(category.title) for category in product.categories.filter(deleted_at__isnull=True)]), product.price, product.is_on_sale, product.discount_amount, product.discount_percent, product.quantity, product.summary, product.description, ';'.join([str(tag.title) for tag in product.tags.filter(deleted_at__isnull=True)]), ','.join([str(image.photo.url) for image in product.photos.filter(deleted_at__isnull=True)]),product.reference_code])
        return response

class ExportUserCSV(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Users.csv"'
        writer = csv.writer(response)
        writer.writerow(['Username', 'Name', 'ID', 'Created Date', 'Email'])
        users = CustomUser.objects.all()
        for user in users: 
            writer.writerow([
                user.username, user.first_name, user.id, user.date_joined, user.email])
        return response


class AssignTitlePhoto(SuccessMessageMixin, BaseMixin, TemplateView):
    template_name = 'cart/assign_title_photo.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['prod_id'])
        return super(AssignTitlePhoto, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.request.method == 'POST':
            img = self.request.POST.get('img_id')

            img_obj = get_object_or_404(Photo, id=img)
            img_obj.is_title_photo = True
            img_obj.save()
            qs = self.product.photos.all().exclude(id=img_obj.id)
            for obj in qs:
                image = get_object_or_404(Photo, id=obj.id)
                image.is_title_photo = False
                image.save()
            return HttpResponseRedirect("/shop/products")
      
        return HttpResponseRedirect("/shop/products")    

    def get_context_data(self, **kwargs):
        context = super(AssignTitlePhoto, self).get_context_data(**kwargs)
        context['object'] = self.product
        return context


class TagCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/tag_form.html'
    model = Tag
    form_class = TagForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:tags")
    success_message = "Tags Successfully Added"

    def form_valid(self, form, **kwargs):
        obj = form.save(commit=False)
        tagsobjects = Tag.objects.filter(title=form.instance.title)
        if not tagsobjects:
            obj.save()
        else: 
             messages.error(self.request, "Tag Already Exist!!!")
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'tags'
        return context


class TagUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    model = Tag
    template_name = 'cart/tag_form.html'
    form_class = TagForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:tags")
    success_message = "Tags Successfully Updated"

    def form_valid(self, form, **kwargs):
        tagsobjects = Tag.objects.filter(title=form.instance.title)
        if not tagsobjects:
            form.save()
        else:
            messages.error(self.request, "Tag Already Exist!!!")
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'tags'
        return context


class TagDeleteView(DeleteMixin):
    """
        Soft deletion
    """
    template_name = 'cart/adminTagsDelete.html'
    model = Tag
    form_class = TagDeleteForm
    success_url = reverse_lazy('cart:tags')


class TagListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/tags.html'
    login_url = "/accounts/adminlogin/"
    queryset = Tag.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'tags'
        context['quick_form'] = QuickActionForm
        return context

class TagsView(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        qs = Tag.objects.all()
        print(qs)
        if self.q:
            qs = qs.filter(title__istartswith=self.q)
        return qs  

class KeywordCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/keyword_form.html'
    model = Keywords
    form_class = KeywordForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:keywords")
    success_message = "Keywords Successfully Added"

    def form_valid(self, form, **kwargs):
        obj = form.save(commit=False)
        keywordsobjects = Keywords.objects.filter(title=form.instance.title)
        if not keywordsobjects:
            obj.slug = form.cleaned_data.get('title').lower().replace(" ", "-")
            obj.save()
        else: 
             messages.error(self.request, "Keyword Already Exist!!!")
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'keywords'
        return context


class KeywordUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    model = Keywords
    template_name = 'cart/keyword_form.html'
    form_class = KeywordForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:keywords")
    success_message = "Keywords Successfully Updated"

    def form_valid(self, form, **kwargs):
        keywordsobjects = Keywords.objects.filter(title=form.instance.title)
        if not keywordsobjects or self.get_object():
            form.save()
        else:
            messages.error(self.request, "Keyword Already Exist!!!")
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'keywords'
        return context


class KeywordDeleteView(DeleteMixin):
    """
        Soft deletion
    """
    template_name = 'cart/adminKeywordsDelete.html'
    model = Keywords
    form_class = KeywordDeleteForm
    success_url = reverse_lazy('cart:keywords')


class KeywordListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/keywords.html'
    login_url = "/accounts/adminlogin/"
    queryset = Keywords.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'keywords'
        context['quick_form'] = QuickActionForm
        return context


class MultipleKeywordDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:keywords")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/keywords')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'keywords', 'option': option, 'ids': id_list, 'urls':url})


class MultipleTagDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:tags")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/tags')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'tag', 'option': option, 'ids': id_list, 'urls':url})


class SliderCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    model = Slider
    template_name = 'cart/slider_form.html'
    form_class = SliderForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:sliders")
    success_message = "Slider Successfully Added"

    def form_valid(self, form, **kwargs):
        sliderobjects = Slider.objects.filter(title=form.instance.title)
        if not sliderobjects:
            form.save()
        else:
            messages.error(self.request, "Slider Already Exist!!!")

        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'slider'
        return context


class SliderUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    model = Slider
    template_name = 'cart/slider_form.html'
    form_class = SliderForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:sliders")
    success_message = "Slider Successfully Updated"

    def form_valid(self, form, **kwargs):
        sliderobjects = Slider.objects.filter(title=form.instance.title).exclude(
            title=self.get_object().title)
        if not sliderobjects:
            form.save()
        else:
            messages.error(self.request, "Slider Already Exist!!!")
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'slider'
        return context


class SliderListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/sliders.html'
    login_url = "/accounts/adminlogin/"
    queryset = Slider.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'slider'
        context['quick_form'] = QuickActionForm
        return context


class SliderDeleteView(DeleteMixin):
    """ Soft deletion """
    template_name = 'cart/slider_delete.html'
    model = Slider
    form_class = SliderDeleteForm
    success_url = reverse_lazy('cart:sliders')


class MultipleSliderDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:sliders")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/sliders')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'slider', 'option': option, 'ids': id_list,'urls':url})



class PhotoList(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/photo_list.html'
    login_url = "/accounts/adminlogin/"
    queryset = Product.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'photo'
        return context


class PhotoUpdate(LoginRequiredMixin, BaseMixin, UpdateView):
    template_name = 'cart/photo_update.html'
    model = Product
    form_class = PhotoForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:products")
    success_message = "Photo Successfully Updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'photo'
        return context

class PhotoDelete(LoginRequiredMixin, BaseMixin, UpdateView):
    def post(self, request, *args, **kwargs):
        if self.request.method == 'POST':
            img = self.request.POST.get('img_id')

            img_obj = get_object_or_404(Photo, id=img)
            img_obj.deleted_at = timezone.now()
            img_obj.save()
            return HttpResponseRedirect("/shop/products")
      
        return HttpResponseRedirect("/shop/products") 


# class DeletePhotos(LoginRequiredMixin, UpdateView):
class DeletePhotos(SuccessMessageMixin, BaseMixin, TemplateView):
    template_name = 'cart/photo_update.html'

    def dispatch(self, request, *args, **kwargs):
        self.product = get_object_or_404(Product, id=kwargs['prod_id'])
        return super(DeletePhotos, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if self.request.method == 'POST':
            if 'selected[]' in self.request.POST:
                imgs = self.request.POST.getlist('selected[]')
                for img in imgs:
                    img_obj = get_object_or_404(Photo, id=img)
                    img_obj.deleted_at = timezone.now()
                    img_obj.save()
                    self.product.photos.remove(img_obj)
                return HttpResponseRedirect("/shop/products")
            return HttpResponseRedirect("/shop/products")    
        return HttpResponseRedirect("/shop/products")    

    def get_context_data(self, **kwargs):
        context = super(DeletePhotos, self).get_context_data(**kwargs)
        context['object'] = self.product
        return context


class AdminSiteConfigCreateView(
        LoginRequiredMixin, SuccessMessageMixin, BaseMixin, CreateView):
    model = SiteConfig
    template_name = 'cart/adminSiteConfigCreate.html'
    login_url = "/accounts/adminlogin/"
    form_class = SiteConfigForm
    success_url = reverse_lazy("message:admin_message")
    success_message = "Site Config Successfully Added"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'site_config'
        return context


class AdminSiteConfigUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/adminSiteConfigUpdate.html'
    model = SiteConfig
    form_class = SiteConfigForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("message:admin_message")
    success_message = "Site Config Successfully Updated"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'site_config'
        return context


class AdminSiteConfigListView(LoginRequiredMixin, BaseMixin, ListView):
    model = SiteConfig
    template_name = 'cart/adminSiteConfigList.html'
    login_url = "/accounts/adminlogin/"
    context_object_name = 'siteConfigs'

    def get_queryset(self):
        return SiteConfig.objects.filter(deleted_at=None)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'site_config'
        return context


class FeaturedProductCreateView(LoginRequiredMixin, SuccessMessageMixin, BaseMixin, CreateView):
    model = FeaturedProduct
    template_name = 'cart/featured_product_form.html'
    form_class = FeaturedProductForm
    success_url = reverse_lazy("cart:featured_product_list")
    success_message = "Featured Product Successfully Added"

    def form_valid(self, form, **kwargs):
        FeaturedProductObjects = FeaturedProduct.objects.filter(products=form.instance.products)
        if not FeaturedProductObjects:
            form.instance.slug = slugify(form.instance.products)
            form.save()
        else:
            messages.error(self.request, "FeaturedProduct Already Exist!")
            return redirect('cart:featured_product_create')

        return super(FeaturedProductCreateView, self).form_valid(form, *kwargs)


class FeaturedProductListView(LoginRequiredMixin, BaseMixin, ListView):
    model = FeaturedProduct
    template_name = 'cart/featured_products.html'
    context_object_name = 'FeaturedProducts'
    queryset = FeaturedProduct.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'featured'
        name = []
        for featured_product in FeaturedProduct.objects.all():
            products = str(featured_product.products)
            name.append(products)


        context['objectlist'] = Product.objects.filter(deleted_at__isnull=True).exclude(name__in=name )
        context['quick_form'] = QuickActionForm

        return context  


class FeaturedProductUpdateView(LoginRequiredMixin, SuccessMessageMixin, BaseMixin, UpdateView):
    model = FeaturedProduct
    template_name = 'cart/featured_product_form.html'
    form_class = FeaturedProductForm
    success_url = reverse_lazy("cart:featured_product_list")
    success_message = "Featured Product Successfully Updated"

    def form_valid(self, form, **kwargs):
        form.save()
        return super(FeaturedProductUpdateView, self).form_valid(form, *kwargs)


class FeaturedProductDeleteView(DeleteView, BaseMixin, SuccessMessageMixin):
    template_name = 'cart/delete_featured_product.html'
    model = FeaturedProduct
    success_url = reverse_lazy("cart:featured_product_list")
    success_message = "Featured Product deleted successfully"


class MultipleFeaturedProductDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:featured_product_list")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/featured_product/list')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'featuredproduct', 'option': option, 'ids': id_list, 'urls':url})


class UsersListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/users.html'
    model = CustomUser

    def get_queryset(self):
        queryset = CustomUser.objects.filter(is_active=True).order_by('-date_joined')
        return queryset

    def get_context_data(self, **kwargs):
        CustomUser.objects.filter(is_read=False).update(is_read=True)
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'UserProfiles'
        return context


class UserCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/user_form.html'
    model = CustomUser
    form_class = UserForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:users")
    success_message = "User Successfully Added"

    def form_valid(self, form, **kwargs):
        user = CustomUser.objects.filter(username=form.instance.username)
        print('asnns')
        if not user:
            user = form.save()
            password = get_random_string(length=10)
            user.set_password(password)
            user.is_active = True
            user.username = user.email.split('@')[0]
            user.save()
            grp = Group.objects.get(name='Customer')
            grp.user_set.add(user)
            mail_subject = 'Your Credentials'
            message="Your username is: "+user.username+" and password: "+password
            to_email = user.email
            email = EmailMessage(mail_subject,message,to=[to_email])
            email.send()
        else:
            messages.error(self.request, "Username Already Exist!!!")
            return redirect('cart:user_create')

        return super().form_valid(form, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'user'
        return context


class UserUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/user_form.html'
    model = CustomUser
    form_class = UserForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:users")
    success_message = "User Successfully Updated"

    def form_valid(self, form, **kwargs):
        user = CustomUser.objects.filter(username=form.instance.username).exclude(
            username=self.get_object().username)
        if not user:
            form.save()
        else:
            messages.error(self.request, "Username Already Exist!!!")
            return redirect('cart:user_create')
        return super().form_valid(form, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'user'
        return context


class UserDelete(SuccessMessageMixin, BaseMixin, UpdateView):
    template_name = 'cart/delete_user.html'
    model = CustomUser
    form_class = UserDeleteForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:users")
    success_message = "User deleted successfully"

    def form_valid(self, form):
        form.instance.is_active = False
        form.save()
        return super().form_valid(form)


class UserPwdResetView(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        user = CustomUser.objects.get(pk=self.kwargs['userId'])
        password = get_random_string(20)
        user.set_password(password)
        user.save()
        msg = 'Hey ' + user.first_name +', '+'your new password for breadfruit is ' + password + ' Please use this from now on.'

        from_email = settings.EMAIL_HOST_USER
        send_mail(
            'Password Reset', msg, from_email, [user.email])
        messages.success(request, "Action Successful ! The New Password has been sent to the registered e-mail")
        return HttpResponseRedirect('/shop/users/')


class UserDetail(LoginRequiredMixin, BaseMixin, DetailView):
    template_name = 'cart/user_detail.html'
    model = CustomUser



def export_customer_detail(request, **kwargs):
    template = get_template("cart/customer_pdf.html")
    customer_id = kwargs['customer_id']
    user = CustomUser.objects.get(id=customer_id)
    html = template.render({'user': user})
    Context({'pagesize':'A4'}) 
    result = BytesIO() 
    pdf = pisa.CreatePDF(StringIO(html), result) 
    if not pdf.err: 
        return HttpResponse(result.getvalue(), content_type='application/pdf') 
    else: 
        return HttpResponse('Errors')
    return response


class FeaturedProductList(ListView):
    template_name = 'layouts/frontend/featured_product_by_category.html'

    def dispatch(self, request, *args, **kwargs):
        self.cat_id = self.kwargs["cat_id"]
        return super().dispatch(request, *args, **kwargs)

    def queryset(self):
        queryset = Product.objects.filter(
            categories=self.cat_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.queryset()
        context['featured_products'] = FeaturedProduct.objects.all()
        return context


class OrdersListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/orders.html'
    model = Order
    login_url = "/accounts/adminlogin/"
    queryset = Order.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'orders'
        context['orderlistt'] = Order.objects.all()
        context['categories'] = Category.objects.filter(deleted_at=None)
        context['quick_form'] = QuickActionForm
        context['form'] = OrderStatusUpdateForm
        context['orderCMSForm'] = OrderFormCMS
        return context


class OrdersFilterView(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):      
        name = self.request.GET['product']
        category = self.request.GET['category']
        daterange = self.request.GET['daterange']
        start = (daterange.split(' - ')[0])
        end = daterange.split(' - ')[1]
        startdate = datetime.datetime.strptime(start, "%m/%d/%Y").strftime("%Y-%m-%d")
        enddate = datetime.datetime.strptime(end, "%m/%d/%Y").strftime("%Y-%m-%d")
        categories = Category.objects.filter(title=category, deleted_at=None)
        products = ProductInTransaction.objects.filter(products__name__icontains=name, deleted_at=None)
        if categories:
            products = products.filter(products__categories__in=categories)
        orders = Order.objects.filter(created_at__range=[startdate, enddate], deleted_at=None)
        if products:
            orders = orders.filter(products__in=products)
        return render(self.request, 'cart/orders.html', {'object_list':orders}) 

class ExportOrderCSV(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(['User', 'Products', 'Quantity', 'Condition'])
        orders = Order.objects.filter(deleted_at__isnull=True)
        for order in orders: 
            writer.writerow([
                order.user, ','.join([product.products.name for product in order.products.all()]),','.join([str(product.quantity) for product in order.products.all()]), order.condition_status])
        return response


def export_order_list(request, **kwargs):
    template = get_template("cart/order_pdf.html")
    Context({'pagesize':'A4'})
    order = Order.objects.filter(deleted_at__isnull=True)
    html = template.render({'orders': order})
    result = BytesIO() 
    pdf = pisa.CreatePDF(StringIO(html), result) 
    if not pdf.err: 
        return HttpResponse(result.getvalue(), content_type='application/pdf') 
    else: 
        return HttpResponse('Errors')
    return response

class OrdersUpdateStatusView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/orders.html'
    model = Order
    form_class = OrderStatusUpdateForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:orders")

    def send_notification(self, user, recipient, verb, action_object, description):
        if recipient:
            notify.send(user, recipient=recipient, verb=verb, action_object=action_object, description=description)

    def form_valid(self, form):
        user = CustomUser.objects.filter(is_superuser=True).first()
        condition_status = form.cleaned_data['condition_status']
        shipped_date = form.cleaned_data['shipped_date']
        condition_status = str(condition_status)
        print('aascass')

        if condition_status == 'Order Placed':
            obj = form.save()
            products = self.get_object().products.all()
            for prod in products:
                try:
                    prod_obj = Product.objects.get(id=prod.products.id)
                    prod_obj.quantity = int(prod_obj.quantity) - (prod.quantity)
                    print(prod_obj.quantity)
                    prod_obj.save()
                except Product.DoesNotExist:
                    pass
            self.send_notification(
                user, recipient=obj.user, verb='Your order has been Placed', action_object=obj,
                description='order')
            messages.success(self.request,"Order " + str(obj.condition_status) + " Successfully")

        elif condition_status == 'Delivered':
            obj = form.save()
            Sales.objects.create(order=obj, delivered_date=obj.shipped_date)
            if obj.user.is_active:
                point_count = obj.total // 100
                try:
                    point_obj = Point.objects.get(user=obj.user)
                    point_obj.total_point += float(point_count)
                    point_obj.save()
                except Point.DoesNotExist:
                    point_obj = Point.objects.create(user=obj.user, total_point=float(point_count))

                valid_from = datetime.datetime.today()
                valid_to = datetime.datetime.today() + datetime.timedelta(days=60)
                code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
                if point_obj.total_point >= 100:
                    coupon = Coupon.objects.create(
                        user=obj.user, title='Points Reward', discount_amount=100, valid_from=valid_from,
                        valid_to=valid_to, code=code)
                    self.send_notification(
                        user, recipient=obj.user, verb='You have got coupon', action_object=coupon,
                        description='coupon')
                    point_obj.total_point -= 100
                    point_obj.save()
            # products = self.get_object().products.all()
            # for prod in products:
            #     try:
            #         prod_obj = Product.objects.get(id=prod.products.id)
            #         prod_obj.quantity -= prod.quantity
            #         prod_obj.save()
            #     except Product.DoesNotExist:
            #         pass

            self.send_notification(
                user, recipient=obj.user, verb='Your order has been delivered', action_object=obj,
                description='order')
            messages.success(self.request,"Order " + str(obj.condition_status) + " Successfully")

        elif condition_status == 'Refunded with Stock':
            obj = form.save()
            messages.success(self.request,"Order Refunded Successfully")
            return HttpResponseRedirect('/orders')
                
        elif condition_status == 'Ready to Ship':
            obj = form.save()
            sales = Sales.objects.create(order=obj, delivered_date=obj.shipped_date)
            messages.success(self.request,"Order Shipped Successfully")
            return HttpResponseRedirect('/shop/bill/'+str(obj.id))

        elif condition_status == 'Cancelled':
            obj = form.save()
            products = self.get_object().products.all()
            for prod in products:
                try:
                    prod_obj = Product.objects.get(id=prod.products.id)
                    prod_obj.quantity += prod.quantity
                    prod_obj.save()
                except Product.DoesNotExist:
                    pass
            self.send_notification(
                user, recipient=obj.user, verb='Your order has been Cancelled', action_object=obj,
                description='order')
            messages.success(self.request,"Order " + str(obj.condition_status) + " Successfully")


        else:
            obj = form.save()
        for product in obj.products.all():
            product.products.order_count += 1
            product.products.save()
        messages.success(self.request,"Order " + str(obj.condition_status) + " Successfully")

        return HttpResponseRedirect(reverse_lazy("cart:orders"))


    def form_invalid(self, form):
        print(form.errors)
        return super().form_invalid(form)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'orders'
        return context

class OrdersUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/order_form.html'
    model = Order
    form_class = OrderForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:orders")
    success_message = "Order Detail Updated Successfully"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        name = []
        total = 0
        discount = 0
        vat = 0
        for product in self.get_object().products.all(): 
            print(product)
            prod = str(product.products.name)  
            name.append(prod)
            total_amt = product.products.price * product.quantity
            total = total + total_amt
            discount_amt = float(total_amt*product.products.discount_percent)/100
            discount = discount + discount_amt
            vat_amt = (float(total_amt-discount_amt)*product.products.vat)/100
            vat = vat+ vat_amt
        context['total'] = total
        context['discount'] = discount
        context['vat'] = vat
        context['grand_total'] = total - discount + vat
        print(discount, vat)
        context['sub_total'] = self.get_object().total
        context['products'] = Product.objects.filter(deleted_at__isnull=True).exclude(name__in=name)
        return context


class OrderProductAdd(SuccessMessageMixin, CreateView):
    model = Order
    form_class= OrderForm
    template_name = "cart/todaydeal.html"

    def form_valid(self, form):
        product = Product.objects.filter(pk= self.kwargs['pk1']).first()
        obj = Order.objects.filter(pk=self.kwargs['pk2']).first()
        products = ProductInTransaction.objects.filter(products=product).first()
        if products == None:
            products = ProductInTransaction.objects.create(products=product)
            product.quantity = product.quantity - products.quantity
            product.save()
        else:
            product.quantity = product.quantity - products.quantity    
            product.save()
        for prod in obj.products.all():            
            obj.products.add(products)
        obj.save()

        messages.success(self.request,"Product Added Successfully")
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

    def form_invalid(self,form):
        return super().form_invalid(form)


class OrderProductDeleteView(SuccessMessageMixin, DeleteMixin):
    template_name = 'cart/orders_product_delete.html'
    model = Order
    form_class = OrderProductDeleteForm

    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        context['product_id'] = self.kwargs.get('product_id')
        return context

    def form_valid(self, form):

        product_id = self.kwargs.get('product_id')
        order_id = self.kwargs.get('pk')
        order = Order.objects.get(pk = order_id)
        product = ProductInTransaction.objects.get(pk=product_id)
        prod = Product.objects.filter(pk=product.products.pk).first()
        prod.quantity = int(prod.quantity) + product.quantity
        prod.save()
        order.products.remove(product)
        order.save()
        messages.success(self.request, "Product Deleted Successfully")
        return redirect('cart:orders_update', pk=order_id)



class OrderProductUpdateQuantityView(BaseMixin,View):

    def get(self, request, *args, **kwargs):
        product_pk = request.GET.get('product_pk')
        qty=None;
        order_id = request.GET.get('order_id')

        order = get_object_or_404(Order, pk=order_id)


        if request.GET.get('qty'):
            qty = int(request.GET.get('qty'))

   
        obj = get_object_or_404(ProductInTransaction,pk=product_pk)
        
        if qty:
            product = Product.objects.filter(pk=obj.products.pk).first()
            product.quantity = int(product.quantity) - qty + int(obj.quantity)
            product.save()
            obj.quantity = qty
            obj.save()
        
        total = 0.0
        for pit in order.products.all():
            total += pit.products.price * pit.quantity

        return JsonResponse({
            'message': 'Success', 'total':total
        })


class OrderRefundView(LoginRequiredMixin, BaseMixin, View):

    def post(self, request, *args, **kwargs):
        order = Order.objects.filter(pk=self.kwargs.get('pk')).first()
        if self.request.is_ajax():
            refund_products = self.request.POST
            if 'values' in refund_products:
                for product in json.loads(refund_products.get('values')):
                    refund_id = product.get('id')
                    product_id = product.get('product_id')
                    quantities = product.get('quantity')

                    try:
                        pit = ProductInTransaction.objects.get(id=int(product_id))
                        prod = Product.objects.get(id=pit.products.id)
                        if refund_id == '' or refund_id == None:
                            # create new refund
                            obj = ProductRefund.objects.create(products_id=int(product_id), quantity=int(quantities))
                            order.refund.add(obj)
                            if int(pit.quantity) >= int(quantities):
                                prod.quantity = int(prod.quantity) + int(quantities)
                                prod.save()
                                pit.quantity = int(pit.quantity) - int(quantities)
                                order.total = float(order.total) - float(prod.price) * int(quantities)
                                pit.save()
                            else:
                                response = {'message':'Quantity exceeds its limit'}
                                return JsonResponse(response)
                        else:
                            # update refund
                            refundobj = ProductRefund.objects.filter(pk=int(refund_id)).first()
                            refund_obj = ProductRefund.objects.filter(pk=int(refund_id)).update(products_id=int(product_id), quantity=int(quantities))
                            if int(pit.quantity) >= int(quantities):
                                prod.quantity = int(prod.quantity) + int(quantities) - int(refundobj.quantity)
                                prod.save()
                                pit.quantity = int(pit.quantity) - int(quantities) + int(refundobj.quantity)
                                pit.save()
                                order.total = float(order.total) - float(prod.price) * int(quantities) + float(prod.price) * int(refundobj.quantity)
                            else:
                                response = {'message':'Quantity exceeds its limit'}
                                return JsonResponse(response)
                    except:
                       pass
        order.condition_status = Status.objects.filter(name="Refunded with Stock").first()
        order.save()
        messages.success(request, "Order Refunded Successfully")
        return HttpResponseRedirect('/orders')



class BillView(LoginRequiredMixin, BaseMixin, TemplateView):
    template_name = 'cart/bill.html'

    def get_context_data(self, **kwargs):
        context = super(BillView, self).get_context_data(**kwargs)
        self.order = Order.objects.get(id=kwargs['order_id'])
        name = []
        total = 0
        discount = 0
        vat = 0
        for product in self.order.products.all(): 
            print(product)
            prod = str(product.products.name)  
            name.append(prod)
            total_amt = product.products.price * product.quantity
            total = total + total_amt
            discount_amt = float(total_amt*product.products.discount_percent)/100
            discount = discount + discount_amt
            vat_amt = (float(total_amt-discount_amt)*product.products.vat)/100
            vat = vat+ vat_amt
        context['total'] = total
        context['discount'] = discount
        context['vat'] = vat
        context['grand_total'] = total - discount + vat
        print(discount, vat)
        context['products'] = Product.objects.filter(deleted_at__isnull=True).exclude(name__in=name)
        context['object'] = self.order
        return context


def bill_generation(request, **kwargs):
    template = get_template("cart/bill_generation.html")
    order = Order.objects.get(id=kwargs['order_id'])
    tender = request.GET.get('tender')
    total = 0
    discount = 0
    vat = 0
    for product in order.products.all(): 
        prod = str(product.products.name)  
        total_amt = product.products.price * product.quantity
        total = total + total_amt
        discount_amt = float(total_amt*product.products.discount_percent)/100
        discount = discount + discount_amt
        vat_amt = (float(total_amt-discount_amt)*product.products.vat)/100
        vat = vat+ vat_amt
    grand_total = total - discount +vat
    html = template.render({
        'object': order, 'discount': discount, 'vat':vat, 'total': total, 'tender': tender, 'return_amt': float(tender)-grand_total,
        'today': timezone.now().date(), 'bill': order.code, 'grand_total':grand_total})    
    Context({'pagesize':'A4'}) 
    result = BytesIO() 
    pdf = pisa.CreatePDF(StringIO(html), result) 
    if not pdf.err: 
        return HttpResponse(result.getvalue(), content_type='application/pdf') 
    else: 
        return HttpResponse('Errors')
    return response
    # response = HttpResponse(content_type='application/pdf')
    # response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # pisaStatus = pisa.CreatePDF(
    #   html, dest=response)
    # # if error then show some funy view
    # if pisaStatus.err:
    #   return HttpResponse('We had some errors <pre>' + html + '</pre>')
    # return response


class AdminOrderDetailView(LoginRequiredMixin, BaseMixin, DetailView):
    template_name = 'cart/order_detail.html'
    model = Order
    login_url = "/accounts/adminlogin/"
    # queryset = Order.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'orderDetails'
        ordered_products = self.get_object().products.all()
        ordered = self.get_object().products.first()
        context['ordered_products'] = ordered.productrefund_set.all()
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


class SalesListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/sales.html'
    model = Sales
    login_url = "/accounts/adminlogin/"
    queryset = Sales.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'sales'
        context['form'] = ExportForm
        context['categories'] = Category.objects.filter(deleted_at=None)
        return context


def export_view(request):
    from_date = request.GET.get('from_date', None).replace(" ","")
    to_date = request.GET.get('to_date', None).replace(" ","")
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales.csv"'
    writer = csv.writer(response)
    writer.writerow(['Customer', 'Products', 'Delivered On', 'Amount'])
    if from_date and to_date:
        sales = Sales.objects.filter(
            deleted_at=None, delivered_date__gte=from_date,
            delivered_date__lte=to_date)
    elif from_date and not to_date:
        sales = Sales.objects.filter(
            delivered_date__gte=from_date, deleted_at=None)
    elif to_date and not from_date:
        sales = Sales.objects.filter(
            delivered_date__lte=to_date, deleted_at=None)
    else:
        sales = Sales.objects.filter(deleted_at=None)
    total_amount = 0
    for obj in sales:
        total_amount += obj.order.total
    for sale in sales:
        products = [product.products.name for product in sale.order.products.all()]
        writer.writerow([
            sale.order.user, products, sale.delivered_date, sale.order.total])
    writer.writerow(['Total Amount', '', '', total_amount])
    return response


class SalesFilterView(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):      
        name = self.request.GET['product']
        category = self.request.GET['category']
        daterange = self.request.GET['daterange']
        start = (daterange.split(' - ')[0])
        end = daterange.split(' - ')[1]
        startdate = datetime.datetime.strptime(start, "%m/%d/%Y").strftime("%Y-%m-%d")
        enddate = datetime.datetime.strptime(end, "%m/%d/%Y").strftime("%Y-%m-%d")
        categories = Category.objects.filter(title=category, deleted_at=None)
        products = ProductInTransaction.objects.filter(products__name__icontains=name, deleted_at=None)
        if categories:
            products = products.filter(products__categories__in=categories)
        orders = Order.objects.filter(created_at__range=[startdate, enddate], deleted_at=None)
        if products:
            orders = orders.filter(products__in=products)
        sales = Sales.objects.filter(order__in=orders, deleted_at=None)
        categories = Category.objects.filter(deleted_at=None)
        return render(self.request, 'cart/sales.html', {'object_list':sales, 'categories':categories}) 


class StatusCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/status_form.html'
    model = Status
    form_class = StatusForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:status")
    success_message = "Status Successfully Added"

    def form_valid(self, form, **kwargs):
        obj = Status.objects.filter(name=form.instance.name)
        if not obj:
            form.save()
        else:
            messages.error(self.request, "Status Already Exist!!!")
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'status'
        return context


class StatusUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/status_form.html'
    model = Status
    form_class = StatusForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:status")
    success_message = "Status Successfully Updated"

    def form_valid(self, form, **kwargs):
        obj = Status.objects.filter(name=form.instance.name)
        form.save()
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'status'
        return context


class StatusDeleteView(DeleteMixin):
    """ Soft deletion """
    template_name = 'cart/status_delete.html'
    model = Status
    form_class = StatusDeleteForm
    success_url = reverse_lazy('cart:status')


class StatusListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/status.html'
    login_url = "/accounts/adminlogin/"
    queryset = Status.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'status'
        context['quick_form'] = QuickActionForm
        return context


class MultipleStatusDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:status")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/status')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'status', 'option': option, 'ids': id_list})


class CreateStatusView(LoginRequiredMixin, BaseMixin, View):

    def post(self, request, *args, **kwargs):
        form = StatusAutoForm(request.POST)
        if form.is_valid():
            obj = form.save()
            return JsonResponse({'id': obj.id }, status=200)
        else:
            return HttpResponse('helllo')


class TrackerUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/tracker_form.html'
    model = Tracker
    form_class = TrackerForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:tracker")
    success_message = "Tracker Successfully Updated"

    def post(self, request, **kwargs):
        if request.method == 'POST':
            status_list = []
            remarks = request.POST['remarks']
            estimated_date = request.POST['estimated_date']
            tracker_obj = self.get_object()
            tracker_obj.remarks = remarks
            tracker_obj.estimated_date = estimated_date
            tracker_obj.save()

            for obj in request.POST.getlist('status'):
                if obj.isdigit():
                    try:
                        status_obj = Status.objects.get(id=obj)
                    except Status.DoesNotExist:
                        pass
                else:
                    status_obj, created = Status.objects.get_or_create(name=obj)
                status_list.append(str(status_obj.id))
            for status in status_list:
                sobj = Status.objects.get(id=status)
                tracker_obj.status.add(sobj)
        return HttpResponseRedirect(reverse("cart:trackers"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'trackers'
        return context


class TrackerListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/trackers.html'
    login_url = "/accounts/adminlogin/"
    queryset = Tracker.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'trackers'
        return context


class InquiryListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/inquiries.html'
    model = Inquiry
    login_url = "/accounts/adminlogin/"
    queryset = Inquiry.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'inquiries'
        context['quick_form'] = QuickActionForm
        return context



class InquiryDetailView(LoginRequiredMixin, BaseMixin, DetailView):
    template_name = 'cart/inquiry_detail.html'
    model = Inquiry
    login_url = "/accounts/adminlogin/"
    queryset = Inquiry.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'inquiries'
        obj = self.get_object()
        obj.is_read = True
        obj.save()
        return context


class InquiryRespondBack(SuccessMessageMixin, BaseMixin, UpdateView):
    template_name = 'cart/respond_back.html'
    model = Inquiry
    form_class = InquiryRespondForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:inquiries")
    success_message = "Inquiry responded"

    def form_valid(self, form):
        form.instance.is_responded = True
        form.save()
        return super(InquiryRespondBack, self).form_valid(form)

class MultipleInquiryDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:inquiries")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/inquiries/')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'inquiry', 'option': option, 'ids': id_list, 'urls':url })

class ReviewListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/reviews.html'
    model = Rating
    login_url = "/accounts/adminlogin/"
    queryset = Rating.objects.filter(deleted_at__isnull=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        Rating.objects.filter(deleted_at__isnull=True).update(is_read=True)
        context = super().get_context_data(**kwargs)
        context['quick_form'] = QuickActionForm
        context['url_name'] = 'rating'
        return context

class MultipleReviewsDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:reviews")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/reviews')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'rating', 'option': option, 'ids': id_list,'urls':url })

class ApproveReview(SuccessMessageMixin, BaseMixin, UpdateView):
    template_name = 'cart/approve_review.html'
    model = Rating
    form_class = ApproveReviewForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:reviews")

    def form_valid(self, form):
        form.save()
        if form.instance.is_approved == True:
            messages.success(self.request, "Review approved successfully")
        else:
            messages.error(self.request, "Review unapproved successfully")
        return super().form_valid(form)


class ProductSearchList(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/search_product.html'
    model = Product
    login_url = "/accounts/adminlogin/"
    context_object_name = 'products'
    queryset = Product.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'search_product'
        return context


class SelectionForOrder(LoginRequiredMixin, TemplateView, BaseMixin):
    template_name = 'cart/order_form_cms.html'

    def get(self, request, *args, **kwargs):
        id_list = request.GET.getlist('selecting')
        self.products = []
        for obj in id_list:
            product = Product.objects.get(id=obj)
            pit = ProductInTransaction.objects.create(products=product)
            self.products.append(pit)
        message_count = Message.objects.filter(deleted_at=None, is_read=False).count()
        inquiries_count = Inquiry.objects.filter(deleted_at=None,is_responded=False, is_read=False).count()
        notify_me = NotifyMe.objects.filter(deleted_at__isnull=True, is_read=False).count()
        users= CustomUser.objects.filter(is_active=True, is_read=False).count()
        reviews= Rating.objects.filter(deleted_at__isnull=True, is_read=False).count()
        subscribers= Subscriber.objects.filter(deleted_at__isnull=True, is_read=False).count()
        orders_count = Order.objects.filter(deleted_at=None, condition_status__name='Order Placed').count()
        url_name = 'messages'
        if self.request.user.is_authenticated:
            notifications = self.request.user.notifications.unread()
            notifications_count = notifications.count()
        return render(request, 'cart/order_for_cms.html', {
        'products': self.products, 'form': OrderFormCMS(), 'message_count':message_count, 'inquiries_count':inquiries_count, 
        'orders_count':orders_count, 'notifications_count': notifications_count, 'notify_me': notify_me, 'users': users, 'reviews': reviews,'subscribers':subscribers  })

    def post(self, request, *args, **kwargs):
        total = 0
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        shipped_date = request.POST.get('shipped_date')
        order = Order.objects.create(
            email=email, contact_number=contact_number, condition_status= Status.objects.get(name= "Delivered"), shipped_date= shipped_date,  code= ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]))
        messages.success(request, "An order has been successfully created.")

        product = request.POST.getlist('product')
        qty = request.POST.getlist('quantity')
        data = dict(zip(product, qty))
        for key, value in data.items():
            obj = ProductInTransaction.objects.get(id=int(key))
            obj.quantity = value
            obj.save()
            total += int(obj.quantity) * int(obj.products.grand_total)
            order.products.add(obj)
            obj.products.quantity = int(obj.products.quantity) - int(obj.quantity)

            obj.products.save()
        order.total = total
        order.save()
        Sales.objects.create(order=order, delivered_date=order.shipped_date)
        return HttpResponseRedirect('/shop/bill/'+str(order.id))

class MakeOrder(LoginRequiredMixin, BaseMixin, View):

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        contact_number = request.POST.get('contact_number')
        shipped_date = request.POST.get('shipped_date')
        products = request.POST.get('products')
        user_pk = self.request.user.pk
        user_obj = CustomUser.objects.filter(pk=user_pk).first()
        code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)])
        qty = request.POST.get('quantity')
        products = Product.objects.get(id=products)
        pit = ProductInTransaction.objects.create(products=products, quantity=qty, is_ordered=True, user=user_obj)
        order = Order.objects.create(
            email=email, contact_number=contact_number, condition_status= Status.objects.get(name= "Ready to Ship"),  shipped_date=shipped_date, code=code, user=user_obj)
        order.products.add(pit)
        messages.success(request, "An order has been successfully created.")

        total = 0
        vat = 0
        discount = 0
        for product in order.products.all(): 
            prod = str(product.products.name)  
            total_amt = product.products.price * product.quantity
            total = total + total_amt
            discount_amt = float(total_amt*product.products.discount_percent)/100
            discount = discount + discount_amt
            vat_amt = (float(total_amt-discount_amt)*product.products.vat)/100
            vat = vat+ vat_amt
        order.total = total - discount + vat
        order.save()

        pit.products.quantity = int(pit.products.quantity) - int(pit.quantity)
        pit.products.save()

        Sales.objects.create(order=order, delivered_date=order.shipped_date)
        return HttpResponseRedirect('/shop/bill/'+str(order.id))

    # def form_invalid(self, request, *args, **kwargs):
    #     print(form.errors)
    #     return super().form_invalid(form)


    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     # context['message_count'] = Message.objects.filter(deleted_at=None, is_read=False).count()
    #     context['inquiries_count'] = Inquiry.objects.filter(deleted_at=None,is_responded=False, is_read=False).count()
    #     context['notify_me'] = NotifyMe.objects.filter(deleted_at__isnull=True, is_read=False).count()
    #     context['users'] = CustomUser.objects.filter(is_active=True, is_read=False).count()
    #     context['subscribers'] = Subscriber.objects.filter(deleted_at__isnull=True, is_read=False).count()
    #     context['reviews'] = Rating.objects.filter(deleted_at__isnull=True, is_read=False).count()
    #     context['orders_count'] = Order.objects.filter(deleted_at=None, condition_status__name='Order Placed').count()
    #     context['url_name'] = 'messages'
    #     if self.request.user.is_authenticated:
    #         notifications = self.request.user.notifications.unread()
    #         context['notifications'] = notifications
    #         context['notifications_count'] = notifications.count()
    #     return context

class ConfirmOrderByCMS(UpdateView, BaseMixin):
    template_name = 'cart/orders.html'
    form_class = OrderConfirmByCMS
    model = Order
    success_url = reverse_lazy('cart:orders')

    def post(self, *args, **kwargs):
        order = Order.objects.filter(id= self.kwargs['pk'],deleted_at__isnull=True).first()
        if order.is_confirmed == True:
            order.is_confirmed = False
            order.save()
        else:
            order.is_confirmed = True
            order.save()
        return HttpResponseRedirect('/orders')



class NotifyMeList(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/notifies.html'
    login_url = "/accounts/adminlogin/"
    queryset = NotifyMe.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        NotifyMe.objects.filter(deleted_at__isnull=True).update(is_read=True)
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'notify_me_list'
        context['quick_form'] = QuickActionForm
 
        return context

class NotifyMeDetail(LoginRequiredMixin, BaseMixin, DetailView):
    template_name = 'cart/notifyme_detail.html'
    model = NotifyMe


class NotifyMeUpdateStatus(UpdateView, BaseMixin):
    template_name = 'cart/notify_me_form.html'
    model = NotifyMe
    form_class = NotifyMeUpdateStatusForm
    success_url = reverse_lazy("cart:notify_me_list")
    success_message = "NotifyMe Updated successfully"

class NotifyMeDelete(SuccessMessageMixin, DeleteMixin):
    template_name = 'cart/delete_notify_me.html'
    model = NotifyMe
    form_class = NotifyMeDeleteForm
    success_url = reverse_lazy("cart:notify_me_list")
    success_message = "NotifyMe deleted successfully"


class MultipleNotifyMeDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:notify_me_list")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/shop/notify-me-list')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'notifyme', 'option': option, 'ids': id_list,'urls':url})


class AddQuantityAdmin(SuccessMessageMixin, UpdateView):
    model = Product
    form_class = QuantityAddForm
    template_name = 'cart/change_quantity_admin.html'
    success_url = '/shop/products/'

    def form_valid(self, form):
        obj = form.save(commit=False)
        id = self.kwargs['pk']
        product = get_object_or_404(Product, id=id)
        obj.quantity = obj.quantity + product.quantity

        obj.save() 
        messages.success(self.request,'Quantities has been updated')
        return super().form_valid(form) 

class TodayDeals(SuccessMessageMixin, CreateView):
    model = FeaturedProduct
    form_class= TodayDealForm
    template_name = "/cart/todaydeal.html"
    success_url = reverse_lazy("cart:featured_product_list")

    def form_valid(self, form):
        product = Product.objects.filter(pk= self.kwargs['pk']).first()
        form.products = product
        obj = form.save(commit=False)
        obj.products = product
        obj.save()

        if self.request.is_ajax():
            return JsonResponse({'message': "Todays Deal Added Successfully"})

        messages.success(self.request,"Todays Deal Added Successfully")
        return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))


# class AddPhoto(View):
#     def post(self, request, *args, **kwargs):
#         if request.method == 'POST':
#             form = ProductPhotoForm(request.POST, request.FILES)
#             print(form)
#             obj = form.save()
#             product = Product.objects.get(pk=self.kwargs['prod_id'])
#             product.photos.add(obj)
#             messages.success(self.request,"Photos Added Successfully")
#         return HttpResponseRedirect(self.request.META.get('HTTP_REFERER'))

class AddPhoto(FormView):  
    form_class = ProductPhotoForm
    template_name = 'cart/photo_form.html'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_id'] = self.kwargs.get('prod_id')
        return context
    
    def form_valid(self, form):
        obj = form.save()
        product = Product.objects.get(pk=self.kwargs['prod_id'])
        product.photos.add(obj)
        messages.success(self.request,"Photos Added Successfully")        
        return super().form_valid(form)

    def get_success_url(self):
        if self.request.META.get('HTTP_REFERER'):
            return self.request.META.get('HTTP_REFERER')
        else:
            return reverse_lazy('cart:product_update', kwargs={'prod_id':self.kwargs.get('prod_id') })    


##########################################################################
# Advertisement
##########################################################################


# ADVERTISEMENT LIST VIEW

class AdvertisementListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/advertisement_list.html'
    login_url = "/accounts/adminlogin/"
    queryset = Advertisement.objects.filter(deleted_at__isnull=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'advertisement'
        context['quick_form'] = QuickActionForm
        return context


# ADVERTISEMENT DELETE
class AdvertisementDelete(SuccessMessageMixin, DeleteMixin):
    template_name = 'cart/advertisement_delete.html'
    model = Advertisement
    form_class = AdvertisementDeleteForm
    success_url = reverse_lazy("cart:advertisement_list")
    success_message = "Advertisement Deleted Successfully"


# ADD ADVERTISEMENT
class AdvertisementCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    template_name = 'cart/advertisement_form.html'
    model = Advertisement
    form_class = AdvertisementForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:advertisement_list")

    def form_valid(self, form, **kwargs):
        if (form.cleaned_data.get('ad_type') == 7) and (Advertisement.objects.filter(ad_type=form.cleaned_data.get('ad_type'), deleted_at=None).exists()):
            messages.error(self.request,"Ad already exist")
            return HttpResponseRedirect('/advertisement/list')
        else:
            form.save()
            messages.success(self.request, 'Advertisement Successfully Added')
            return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'advertisement'
        return context


# ADVERTISEMENT UPDATE

class AdvertisementUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    template_name = 'cart/advertisement_form.html'
    model = Advertisement
    form_class = AdvertisementForm
    login_url = "/accounts/adminlogin/"
    success_url = reverse_lazy("cart:advertisement_list")

    def form_valid(self, form, **kwargs):
        if self.get_object().ad_type == 7:
            form.save()
            messages.success(self.request, 'Advertisement Updated Successfully')

        elif (form.cleaned_data.get('ad_type') == 7) and (Advertisement.objects.filter(ad_type=form.cleaned_data.get('ad_type'), deleted_at=None).exists()):
            messages.error(self.request,"Ad already exist")
            return HttpResponseRedirect('/advertisement/list')

        else:
            form.save()
            messages.success(self.request, 'Advertisement Updated Successfully')
        return super().form_valid(form, *kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'advertisement'
        return context

# MULTIPLE ADVERTISEMENT DELETION

class MultipleAdvertisementDeletion(SuccessMessageMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):
        option = request.GET.get('options')
        url =reverse_lazy("cart:advertisement_list")
        url_list = reverse_lazy("cart:advertisement_list")
        if option == 'Not an option':
            messages.error(request, "Choose correct option")
            return HttpResponseRedirect('/list-advertisement')
        else:
            id_list = request.GET.getlist('selecting')
            return render(request, 'cart/multiple_options_confirmation.html', {
                'model': 'advertisement', 'option': option, 'ids': id_list,'urls':url })

class BillCreateView(View):

    def post(self,request,*args, **kwargs):
        order = Order.objects.get(id=kwargs['pk'])
        name = order.user.name
        if order.user.user_shipping_addr:
            address = order.user.user_shipping_addr.all().first().full_address()
        else:
            address = " "

        # if order.user.city:
        #     city = order.user.city
        # else:
        #     city = " "

        if order.user.mobile_number:
             contact_number = order.user.mobile_number
        else:
            contact_number = " "
        # country = request.POST.get('country')
        package_count = order.products.filter(deleted_at__isnull=True).count()

        sender_name = "GAAVA"
        sender_address = "KATHMANDU - 15"
        sender_postal = "KATHMANDU 44600"
        sender_country = "NP"
        sender_code = "Ayata Incorporations Kathmandu - 15 KATHMANDU 44600  NP"
        sender_drop_center_code = "SK 001 01-A"
        sender_mobile = "9849810891"
        # ship = Ship.objects.create(name=name, address=address, postal_address = postal_address, country= country)
        sender,_ = Sender.objects.get_or_create(sender_line_1=sender_name, sender_phone=sender_mobile, address= sender_address, postal_address=sender_postal, country= sender_country,sender_code=sender_code, sender_drop_center_code=sender_drop_center_code)

        product = []
        images = []
        if request.POST.get('package_weight'):
            package_weight = request.POST.get('package_weight')
        else:
            package_weight = ''
        # for index,wt in enumerate(order.products.all()):
        #     if wt.products.product_weight:
        #         product_weight = product_weight+int(wt.products.product_weight)
        #     else:
        #         product_weight = ""

        tracking_no = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(10)]).upper()
        data = {
            # 'page_no': "{} of {}".format(index+1, package_count),
            'page_no': "",
            'receiver_name': name,
            'receiver_address': address,
            'contact_number' : str(contact_number),
            # 'country': country,
            'package_weight': str(package_weight),
            'tracking_no':tracking_no,
            'sender_line_1':sender_name,
            'sender_line_rem':str(sender_address+"\n"+sender_postal+"\n"+sender_country),
            'sender_code':sender_code,
            'sender_drop_center_code':sender_drop_center_code,
            'sender_mobile':sender_mobile,
            'price':'Rs '+str(order.total)
        }
        
        img = barcode_generator(**data)
        images.append(img)
        # prod = ProductWeight.objects.create(product_wt=wt)
        # ship.product.add(prod)
        OrderTracking.objects.create(order = order, trackingcode=tracking_no)  
        buffer = BytesIO()
        image_save(images, buffer)
        im = InMemoryUploadedFile(buffer, None , "barcode.pdf", "file/pdf", buffer.tell(), None)
        order.label = im
        order.save()
        print(order.label)

        return HttpResponseRedirect("/media/"+str(order.label))

class NotificationsSend(View):
    def get(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')
        product = Product.objects.get(pk=pk)
        print(product)
        if not product:
            if request.is_ajax():
                return JsonResponse({'message':"Product Not found"})
            return HttpResponse("Product Not Found")

        try:
            url = 'https://fcm.googleapis.com/fcm/send'
            headers = {
                'Authorization': 'key=AAAA4wVzG9M:APA91bHu-ahDCGggsqX7BXlo2PD-zHM3m43EfyjIJ2l-yADzDgjCD-ypxdQ-Ya40sSoP85-8fHBCUi5qAuiWwcfloz5BE0AwQWFgEv8tviCXsWcVWJzo9tF-ZA6q6KZ4zmudFxiGaHJ7',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
            json = {
                "notification": {
                    "title": product.name,
                    "body": "This product is available at price "+str(product.price),
                    "sound": "default"
                },
                "priority": "high", 
                "data": {
                    "click_action": "FLUTTER_NOTIFICATION_CLICK", 
                    "id": product.id,
                    "title": product.name,
                    # "bodyText" : "http://breadfruit.me/product/"+str(pk)+"/detail/",
                    "status": "done"
                },
                "to": "/topics/app"
            }
        
            r = requests.post(url, json=json, headers=headers)
            if(r.status_code != 200):
                if request.is_ajax():
                    return JsonResponse({'message':'Sending Notification Failed'})
                return HttpResponse("Sending Notification Failed'")
        except Exception as e:
            if request.is_ajax():
                return JsonResponse({'message':'Sending Notification Failed'})
            return HttpResponse("Sending Notification Failed'")
        if request.is_ajax():
            return JsonResponse({'message':'Sending Notification Successfull'})
        return HttpResponse("Sending Notification Successfull")
            # Failed pushing notification
            # product.notification = False
            # product.save()