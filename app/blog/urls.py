from django.urls import path

from .views import BlogViewSet, GetImageUrlViewSet, BlogCategoryListViewSet

urlpatterns = [
    # List of blog category
    path('category/', BlogCategoryListViewSet.as_view(), name='get_blog_category_list'),
    # Create Blog and List Blogs
    path('', BlogViewSet.as_view({'post': 'create', 'get': 'list'}), name='create_list_blog'),

    # Upload Image
    path('image/upload/', GetImageUrlViewSet.as_view({'post': 'create'}), name="upload"),

    # Retrieve, Update, Delete Blog
    path('<slug:slug>/',
         BlogViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}),
         name='retrieve_update_delete_blog'),

    # path('destroy/<int:pk>/', GetImageUrlViewSet.as_view({'delete': 'destroy'}), name="destroy")
]
