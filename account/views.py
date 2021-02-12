import random
import string
import datetime
import csv, subprocess
from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.generic import (
    TemplateView, View, CreateView, UpdateView, ListView, FormView)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView,
    PasswordResetCompleteView)
# from threading import Thread
from account.models import Subscriber
from cart.models import (
    FeaturedProduct, Cart, Category, Coupon)
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import *
from cart.views import ClientMixin
from notifications.signals import notify

from django.http import HttpResponse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from .models import User
from django.core.mail import EmailMessage
from django.utils.crypto import get_random_string
from cart.views_admin import BaseMixin

from account.models import CURRENT_DOMAIN
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# def handler404(request):
#     return HttpResponseRedirect('/')


class LogoutPage(LoginRequiredMixin, View):
    login_url = "/accounts/adminlogin/"

    def get(self, request):
        logout(request)
        return HttpResponseRedirect('/')


class LoginPage(TemplateView):
    template_name = "account/adminLogin.html"

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            print(username, password)
            user = authenticate(username=username, password=password)
            form = LoginForm()
            users_in_group = Group.objects.get(name="Staff").user_set.all()
            if user is not None and (user.is_superuser or user in users_in_group):
                login(request, user)
                return HttpResponseRedirect('/gaava-admin/')
            else:
                return render(request, self.template_name, {
                    'form': form, 'user': username,
                    'error': 'Incorrect username or password'})


class GaavaBackend(LoginRequiredMixin,  BaseMixin, TemplateView):
    template_name = "dashboard.html"
    login_url = '/accounts/adminlogin/'

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        users_in_group = Group.objects.get(name="Staff").user_set.all()
        context['ourstaff'] = users_in_group
        return context


class GaavaFrontend(ClientMixin, TemplateView):
    template_name = "frontend/index.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['form'] = SubscribeForm
        return context


class RegistrationView(ClientMixin, View):
    def get(self, request):
        form = UserForm()
        context = {'form': form,}
        my_cart = []
        if 'into_cart' in self.request.session:
            for obj_id in self.request.session['into_cart']:
                obj = Cart.objects.get(id=obj_id)
                my_cart.append(obj)
        cart_object = my_cart

        return render(request, 'frontend/register.html', {
            'form': form, 'my_cart': cart_object, 'cart_count': len(cart_object) })

    def post(self, request):
        admin_user = User.objects.filter(is_superuser=True).first()
        form = UserForm(request.POST or None)
        if form.is_valid():
            form.instance.username = form.cleaned_data['email']
            user = form.save(commit=False)
            password = form.cleaned_data.get('password2')
            user.set_password(password)
            try:
                validate_password(password,user)
            except ValidationError as e:
                form.add_error("password1",e)
                return render(request, 'frontend/register.html', {'form':form})    

            user.customer_type = 'Registered'
            user.is_active = False
            user.save()
            grp = Group.objects.get(name='Customer')
            grp.user_set.add(user)
            # current_site = get_current_site(request)
            # message = render_to_string('acc_active_email.html', {
            #     'user': user, 
            #     'domain': CURRENT_DOMAIN,
            #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            #     'token': account_activation_token.make_token(user),
            # })
            # mail_subject = 'Gaava Electronics: Confirm your email address'
            # to_email = user.email
            # email = EmailMessage(mail_subject, message, to=[to_email])
            # email.send()
            # t1 = Thread(target=self.sendmail, args=(user,))
            # t1.start()

            valid_from = datetime.datetime.today()
            valid_to = datetime.datetime.today() + datetime.timedelta(days=60)
            code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)]).lower()
            coupon = Coupon.objects.create(
                user=user, title='Registered', discount_amount=100, valid_from=valid_from,
                valid_to=valid_to, code=code)
            notify.send(
                admin_user, recipient=user, verb='Welcome to the gaava', action_object=coupon,
                description='coupon')
            next = self.request.GET.get('next')
            if next:
                return redirect(next)
                messages.success(request, "A confirmation email has been sent to your account. Please check your email for confirmation") 
            return HttpResponseRedirect(reverse('account:client_login'))

        context = {'form': form}
        return render(request, 'frontend/register.html', context)


class ClientLoginView(TemplateView):
    template_name = 'frontend/login.html'

    def get(self, request):
        form = LoginForm()
        my_cart = []
        if 'into_cart' in self.request.session:
            for obj_id in self.request.session['into_cart']:
                obj = Cart.objects.get(id=obj_id)
                my_cart.append(obj)
        cart_object = my_cart

        return render(request, self.template_name, {
            'form': form, 'my_cart': cart_object, 'cart_count': len(cart_object)})

    def post(self, request):
        form = LoginForm(request.POST or None)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user_is_customer = Group.objects.get(name='Customer').user_set.all()

            try:
                check_user = User.objects.get(username=username)
                user_was_active = check_user.is_active
                if not check_user.is_active:
                    check_user.is_active=True
                    check_user.save()
                user = authenticate(username=username ,password=password)
                print(user, user_was_active)
                # if user != None and user_was_active == True:
                if user != None:
                    print(user)
                    login(request, user)
                    next = self.request.GET.get('next')
                    if next:
                        return redirect(next)
                    return redirect('account:test')
                elif user != None:
                    user.is_active=False
                    # current_site = get_current_site(request)
                    # message = render_to_string('acc_active_email.html', {
                    #     'user': user, 
                    #     'domain': current_site.domain,
                    #     'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    #     'token': account_activation_token.make_token(user),
                    # })
                    # mail_subject = 'Activate your breadfruit account.'
                    # to_email = user.email
                    # email = EmailMessage(mail_subject, message, to=[to_email])
                    # email.send()
                    user.save()
                    # context = {'form': form, 'error': 'A confirmation email has been sent to you'}
                    # return render(request, 'frontend/login.html', context)
                    return HttpResponseRedirect(reverse('account:test'))
                else:
                    # user not match
                    if user_was_active == False:
                        check_user.is_active = False
                        check_user.save()
            except Exception as e:
                pass
            
        context = {'form': form, 'error': 'Incorrect username or password'}
        return render(request, 'frontend/login.html', context)


class LogoutView(View):

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            logout(request)
        return redirect('account:test')

class Deactivate(View):

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated():
            self.request.user.is_active = False
            self.request.user.save()
            logout(request)
        return redirect('account:test')

class ProfileDetailView(View):

    def get(self, request, *args, **kwargs):
        
        # pk = kwargs['pk']
        # user = get_object_or_404(User, username=slug)
        # userProfile = get_object_or_404(UserProfile, user=user)
        ship_addr = ShippingAddress.objects.filter(user=self.request.user)
        context = {}
        context['profile_form'] = UserUpdateForm(instance=self.request.user)
        if ship_addr.exists():
            context['shipping_from'] = ShippingAddressForm(instance=ship_addr[0])
        else:
            context['shipping_from'] = ShippingAddressForm()
        context['changepasswordForm'] = ChangePasswordForm()
            
        
        return render(request, 'account/profileUpdate.html', context)


class ProfileUpdateView(LoginRequiredMixin, ClientMixin, UpdateView):
    template_name = 'account/profileUpdate.html'
    model = User
    form_class = UserUpdateForm

    def form_valid(self, form, **kwargs):
        print('here validated')
        form.save()
        return HttpResponseRedirect(reverse_lazy('account:profile-detail', kwargs={'pk':self.request.user.pk}))

    def form_invalid(self, form, **kwargs):
        print('here validated')
        print(form.errors)
        return super(ProfileUpdateView, self).form_invalid(form, *kwargs)


class AdminStaffListView(LoginRequiredMixin, BaseMixin, ListView):
    model = User
    template_name = 'account/adminStaffList.html'
    login_url = "/accounts/adminlogin/"
    context_object_name = 'staffs'

    def get_queryset(self):
        return User.objects.filter(groups__name='Staff', is_active=True)


class AdminStaffCreateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, CreateView):
    model = User
    form_class = StaffForm
    template_name = 'account/adminStaffCreate.html'
    login_url = "/accounts/adminlogin/"

    def post(self, request):
        staffForm = StaffForm(request.POST or None)
        if staffForm.is_valid():
            user = staffForm.save(commit=False)
            password = get_random_string(length=10)
            user.set_password(password)
            user.is_active = True
            user.save()
            grp = Group.objects.get(name='Staff')
            grp.user_set.add(user)
            username = staffForm.cleaned_data['username']
            mail_subject = 'Your Credentials'
            message="Your username is: "+username+" and password: "+password
            to_email = user.email
            email = EmailMessage(mail_subject,message,to=[to_email])
            email.send()
            messages.success(request, "Registration Successful")
            return redirect('account:adminStaffList')
        context = {
            'staffForm': staffForm,
        }
        return super(AdminStaffCreateView, self).post(self, request)


class AdminStaffUpdateView(LoginRequiredMixin, BaseMixin, SuccessMessageMixin, UpdateView):
    model = User
    template_name = 'account/adminStaffUpdate.html'
    login_url = "/accounts/adminlogin/"
    form_class = StaffForm
    success_url = reverse_lazy("account:adminStaffList")
    success_message = "Staff Successfully Updated"

    def form_valid(self, form, **kwargs):
        staffobject = User.objects.filter(username=form.instance.username)
        if not staffobject:
            form.save()
        else:
            print("repeated")
        return super(AdminStaffUpdateView, self).form_valid(form, *kwargs)


class AdminStaffDeleteView(LoginRequiredMixin, BaseMixin, UpdateView):
    """
        Soft deletion
    """
    template_name = 'account/adminStaffDelete.html'
    login_url = "/accounts/adminlogin/"
    model = User
    form_class = StaffDeleteForm
    success_url = reverse_lazy('account:adminStaffList')

    def form_valid(self, form, **kwargs):
        form.instance.is_active = False
        form.save()
        return super(AdminStaffDeleteView, self).form_valid(form, *kwargs)


class FeaturedProductList(ListView):
    template_name = 'layouts/frontend/featured_product.html'

    def queryset(self):
        queryset = FeaturedProduct.objects.all()
        return queryset

class ReCaptchaMixin:    
    def post(self, request, *args, **kwargs):
        g_recaptcha_response = request.POST.get('g-recaptcha-response')
        if g_recaptcha_response:
            if g_recaptcha_response.strip() != "" :
                return super().post(request, *args, **kwargs)
        messages.warning(self.request, 'Please submit captcha too.')
        return HttpResponseRedirect('/' + str(news.id))


class SubscriberCreate(ReCaptchaMixin, FormView):
    template_name = 'landingpage.html'
    form_class = SubscribeForm
    success_url = '/'

    def form_valid(self, form):
        email = form.cleaned_data.get('email')
        Subscriber.objects.create(email=email)
        subject = "Subscription"
        body = "Thank you for a subscription" 
        from_email = settings.EMAIL_HOST_USER
        send_mail(
            subject, body, from_email, [email]
        )
        return super().form_valid(form)


class SubscribersListView(LoginRequiredMixin, BaseMixin, ListView):
    template_name = 'cart/admin_subscriber_list.html'
    model = Subscriber
    login_url = "/accounts/adminlogin/"
    queryset = Subscriber.objects.filter(deleted_at__isnull=True)

    def get_context_data(self, **kwargs):
        Subscriber.objects.filter(deleted_at__isnull=True).update(is_read=True)
        context = super().get_context_data(**kwargs)
        context['url_name'] = 'subscribers'
        return context


class SubscriberDeleteView(LoginRequiredMixin, UpdateView):
    template_name = 'cart/subscriber_delete.html'
    model = Subscriber
    form_class = SubscriberDeleteForm
    success_url = reverse_lazy('account:subcriber_list')

    def form_valid(self, form):
        form.instance.deleted_at = timezone.now()
        form.save()
        messages.success(self.request, "Subscriber deleted Successfully")
        return super().form_valid(form)




class ExportSubscriberCSV(LoginRequiredMixin, BaseMixin, View):

    def get(self, request, *args, **kwargs):        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
        writer = csv.writer(response)
        writer.writerow(['Subscribers Email','Subscribed Date'])
        subscribers = Subscriber.objects.all()
        for subscriber in subscribers:
            writer.writerow([
                subscriber.email,subscriber.created_at])
        return response


class EmailConfirmation(ClientMixin, TemplateView):
    template_name = "account/email_confirmation.html"


class ResetPasswordRequestView(ClientMixin, PasswordResetView):
    template_name = "account/password_reset_form.html"
    form_class = PasswordResetRequestForm
    success_url = reverse_lazy('account:password_reset_done')


class CustomerPasswordResetDoneView(ClientMixin, PasswordResetDoneView):
    template_name = "account/password_reset_done.html"


class CustomerPasswordResetConfirmView(ClientMixin, PasswordResetConfirmView):
    template_name = "account/password_reset_confirm.html"


class CustomerPasswordResetCompleteView(ClientMixin, PasswordResetCompleteView):
    template_name = "account/password_reset_complete.html"


class ChangePassword(SuccessMessageMixin, FormView):
    model = User
    form_class = ChangePasswordForm
    template_name = 'account/change_password.html'
    success_message = "Logged In with new password"

    def get_form_kwargs(self):
        kwargs = super(ChangePassword, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_success_url(self):
        if self.request.user.groups.filter(name='Staff').exists():
            return  reverse_lazy('account:adminlogin')
        else:
            return reverse_lazy('account:client_login')

    # def form_invalid(self, form):
    #     password = form.cleaned_data.get('password')
    #     user = self.request.user
    #     user.set_password(password)
    #     user.save()
    #     return super(ChangePassword, self).form_invalid(form)

    def form_valid(self, form):
        print(form)
        password = form.cleaned_data.get('password')
        user = self.request.user
        user.set_password(password)
        user.save()
        return super(ChangePassword, self).form_valid(form)


def activate(request, uidb64, token, backend='django.contrib.auth.backends.ModelBackend'):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return HttpResponseRedirect('/')
    else:
        return HttpResponse('Activation link is invalid!')


class UpdateShippingAddress(LoginRequiredMixin, FormView):
    model = ShippingAddress
    form_class = ShippingAddressForm
    template_name = 'layouts/account/profileUpdate.html'

    def form_valid(self, form):
        # form.instance.billing_addr = True
        ship_addr = ShippingAddress.objects.filter(user=self.request.user)
        print(form.cleaned_data)
        if ship_addr.exists():
            ship_addr = ship_addr[0]
            ship_addr.street_name = form.cleaned_data['street_name']
            ship_addr.city = form.cleaned_data['city']
            ship_addr.country = form.cleaned_data['country']
            ship_addr.contact_number = form.cleaned_data['contact_number']
            ship_addr.postal_code = form.cleaned_data['postal_code']
            ship_addr.user = self.request.user
            ship_addr.save()
            print(ship_addr.street_name)
        else:
            form.instance.user = self.request.user
            form.save()
        return HttpResponseRedirect(reverse_lazy('account:profile-detail', kwargs={'pk':self.request.user.pk}))

    def form_invalid(self, form):
        print(form.errors)
        return HttpResponseRedirect(reverse_lazy('account:profile-detail', kwargs={'pk':self.request.user.pk}))