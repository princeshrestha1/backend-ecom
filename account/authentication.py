from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

MyUser = get_user_model()


class UsernameOrEmailorPhoneNoBackend(ModelBackend):
   def authenticate(self, request, username=None, mobile_number=None, password=None, **kwargs):
      try:
         user = MyUser.objects.get(Q(username=username)|Q(email=username)|Q(mobile_number=mobile_number))
         if user.check_password(password):
               return user
      except MyUser.DoesNotExist:
         MyUser().set_password(password)

   def get_user(self, user_id):
      try:
         return MyUser.objects.get(pk=user_id)
      except MyUser.DoesNotExist:
         return None

