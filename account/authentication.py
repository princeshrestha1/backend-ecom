from django.db.models import Q
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

MyUser = get_user_model()


class UsernameOrEmailorPhoneNoBackend(ModelBackend):
   def authenticate(self, request, username=None, mobile_number=None, password=None, **kwargs):
      try:
         # Try to fetch the user by searching the username or email field
         user = MyUser.objects.get(Q(username=username)|Q(email=username)|Q(mobile_number=mobile_number))
         if user.check_password(password):
               return user
      except MyUser.DoesNotExist:
         # Run the default password hasher once to reduce the timing
         # difference between an existing and a non-existing user (#20760).
         MyUser().set_password(password)

   def get_user(self, user_id):
      try:
         return MyUser.objects.get(pk=user_id)
      except MyUser.DoesNotExist:
         return None

