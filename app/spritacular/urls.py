from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from users.views import RootView
from blog.views import ContentManagementViewSet, MeetTheTeamViewSet

urlpatterns = [
    path('', RootView.as_view(), name='root_view'),
    path('admin/', admin.site.urls),
    # path('api-auth/', include('rest_framework.urls')),
    # Users app urls
    path('api/users/', include('users.urls')),
    # Observation app urls
    path('api/observation/', include('observation.urls')),
    # Notification app urls
    path('api/notification/', include('notification.urls')),
    # Only allow creation of devices by authenticated users
    path('api/devices/', FCMDeviceAuthorizedViewSet.as_view({'post': 'create'}), name='create_fcm_device'),
    path('api/blog/', include('blog.urls')),
    path('api/quiz/', include('quiz.urls')),
    path('api/<str:page>/', ContentManagementViewSet.as_view({'post': 'create', 'put': 'update', 'get': 'retrieve'}),
         name='content_management'),
    # List spritacular team
    path('api/team/list_team/', MeetTheTeamViewSet.as_view({'get': 'list'}, name='list_team')),
    # Meet the team CRUD urls start
    path('api/team/add_team_member/', MeetTheTeamViewSet.as_view({'post': 'create'}, name='add_team_member')),
    path('api/team/update_team_member/<int:pk>/', MeetTheTeamViewSet.as_view({'put': 'update'}),
         name='update_team_member'),
    path('api/team/get_team_member/<int:pk>/', MeetTheTeamViewSet.as_view({'get': 'retrieve'}),
         name='get_team_member'),
    path('api/team/delete_team_member/<int:pk>/', MeetTheTeamViewSet.as_view({'delete': 'destroy'}),
         name='delete_team_member'),
    # Meet the team CRUD urls end
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT})
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
