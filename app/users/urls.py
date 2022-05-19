from rest_framework_simplejwt.views import (
    # TokenObtainPairView,
    TokenRefreshView,
)
from django.urls import path, include
from .views import UserRegisterViewSet, ChangePasswordViewSet, LogoutViewSet, CameraSettingsApiView, \
    CustomObtainTokenPairView, RootView

# from rest_framework import routers
# router = routers.DefaultRouter()
# router.register('camera_setting', CameraSettingsApiView, basename='camera_setting')
# urlpatterns = router.urls

urlpatterns = [
    # Login
    path('token/', CustomObtainTokenPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # SignUp
    path('register/', UserRegisterViewSet.as_view({'post': 'create'}), name='register'),
    # User profile image upload or profile update

    path('user_profile/<int:pk>/',
         UserRegisterViewSet.as_view({'patch': 'profile_update', 'get': 'retrieve', 'put': 'update_user_profile'}),
         name='profile_retrieve_update'),
    # Change Password
    path('change-password/<int:pk>/', ChangePasswordViewSet.as_view(), name='change-password'),
    # Password reset
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    # Logout
    path('logout/', LogoutViewSet.as_view(), name='logout'),
    path('camera_setting/'
         , CameraSettingsApiView.as_view({'post': 'create', 'get': 'retrieve', 'patch': 'update'}),
         name='camera_setting'),
    path('user_details/', UserRegisterViewSet.as_view({'get': 'get_user_details'}), name='user_details'),
]
