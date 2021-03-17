# from rest_framework.authentication import TokenAuthentication
# from django.contrib.auth import get_user_model

# class CustomTokenAuth(TokenAuthentication):
#     keyword = 'Bearer'
#     def authenticate_credentials(self,key):
#         User = get_user_model()
#         user=User.objects.get(auth_token=key)
#         return user,key