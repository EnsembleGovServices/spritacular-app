from django.shortcuts import get_object_or_404
from sentry_sdk import capture_exception

import constants
import json

from rest_framework.permissions import IsAuthenticated
from users.permissions import IsAdmin
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import BlogCategory, Blog, BlogImageData, ContentManagement, MeetTheTeam
from .serializers import MeetTheTeamSerializer


class BlogCategoryListViewSet(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        data = []
        for i in BlogCategory.objects.all():
            category_details = {
                'id': i.pk,
                'name': i.title
            }
            data.append(category_details)

        return Response(data, status=status.HTTP_200_OK)


class BlogViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsAdmin] if self.action in ['post', 'put'] else []
        return [permission() for permission in permission_classes]

    def get_object(self, slug):
        try:
            return Blog.objects.get(slug__exact=slug)
        except Blog.DoesNotExist as e:
            capture_exception(e)
            return None

    def list(self, request, *args, **kwargs):
        blog_data = []

        for i in Blog.objects.filter(article_type=Blog.BLOG).order_by('-created_on'):
            record = {
                "id": i.id,
                "title": i.title,
                "description": i.description,
                "content": i.content,
                "thumbnail_image": i.thumbnail_image.url,
                "category_id": i.category.id if i.category else None,
                "category_name": i.category.title if i.category else None,
                "slug": i.slug,
                "type": i.article_type
            }

            blog_data.append(record)

        return Response({'data': blog_data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        if request.data.get('thumbnail_image') == 'null':
            return Response({'detail': 'Thumbnail image not provided.', 'status': 0},
                            status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get('category'):
            return Response({'detail': 'Category not selected.', 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'article_type': 1,
            'thumbnail_image': request.data.get('thumbnail_image'),
            'user': request.user,
            'title': request.data.get('title'),
            'content': request.data.get('content'),
            'description': request.data.get('description')
        }
        category = request.data.get('category', None)
        category_obj = None
        if category:
            try:
                category_obj = BlogCategory.objects.get(id=category)
            except BlogCategory.DoesNotExist:
                pass
        image_ids_data = request.data.get('image_ids') or '[]'
        image_ids = json.loads(image_ids_data)

        blog_obj = Blog.objects.create(**data, category=category_obj)
        blog_obj.set_slug()

        for i in image_ids:
            BlogImageData.objects.filter(id=i.get('id')).update(is_published=True, blog=blog_obj)

        return Response(constants.BLOG_FORM_SUCCESS, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        blog_obj = self.get_object(kwargs.get('slug'))
        if not blog_obj:
            print("Not found")
            return Response(constants.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)
        if request.data.get('thumbnail_image') == 'null':
            return Response({'detail': 'Thumbnail image not provided.', 'status': 0},
                            status=status.HTTP_400_BAD_REQUEST)
        if not request.data.get('category'):
            return Response({'detail': 'Category not selected.', 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'article_type': 1,
            'thumbnail_image': request.data.get('thumbnail_image'),
            'user': request.user,
            'title': request.data.get('title'),
            'content': request.data.get('content'),
            'description': request.data.get('description')
        }
        category = request.data.get('category', None)
        category_obj = None
        if category:
            try:
                category_obj = BlogCategory.objects.get(id=category)
            except BlogCategory.DoesNotExist:
                pass

        image_ids_data = request.data.get('image_ids') or '[]'
        image_ids = json.loads(image_ids_data)

        blog_obj.title = data.get('title')
        blog_obj.description = data.get('description')
        blog_obj.content = data.get('content')
        blog_obj.article_type = data.get('article_type')
        blog_obj.thumbnail_image = data.get('thumbnail_image')
        blog_obj.category = category_obj
        blog_obj.save()
        blog_obj.set_slug()

        for i in image_ids:
            BlogImageData.objects.filter(id=i.get('id')).update(is_published=True, blog=blog_obj)

        blog_images = BlogImageData.objects.filter(blog=blog_obj)
        for img in blog_images:
            if not Blog.objects.filter(id=blog_obj.id, content__icontains=img.image_file.url).exists():
                img.is_published = False
                img.save(update_fields=['is_published'])

        return Response(constants.BLOG_FORM_SUCCESS, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        blog_obj = self.get_object(kwargs.get('slug'))
        if not blog_obj:
            return Response(constants.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        return Response({"data": {"id": blog_obj.id,
                                  "title": blog_obj.title,
                                  "description": blog_obj.description,
                                  "content": blog_obj.content,
                                  "category": blog_obj.category.id if blog_obj.category else None,
                                  "thumbnail_image": blog_obj.thumbnail_image.url,
                                  "slug": blog_obj.slug}}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        blog_obj = get_object_or_404(Blog, slug=kwargs.get('slug'))
        article_type = "Blog"
        blog_obj.delete()

        return Response({'success': f'{article_type} successfully deleted.', 'status': 1}, status=status.HTTP_200_OK)


class GetImageUrlViewSet(viewsets.ModelViewSet):

    def create(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        blog_image_obj = BlogImageData.objects.create(image_file=image)

        return Response({"uploaded": True,
                         "url": blog_image_obj.image_file.url,
                         "image_id": blog_image_obj.id},
                        status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        try:
            image_obj = BlogImageData.objects.get(pk=kwargs.get('pg'))
        except BlogImageData.DoesNotExist as e:
            capture_exception(e)
            return Response(constants.NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        image_obj.delete()

        return Response({'status': 1}, status=status.HTTP_200_OK)


class ContentManagementViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsAdmin] if self.action in ['post', 'put'] else []
        return [permission() for permission in permission_classes]

    def get_object(self, page_name=None):
        try:
            return ContentManagement.objects.get(type__exact=page_name)
        except ContentManagement.DoesNotExist as e:
            capture_exception(e)
            return None

    def retrieve(self, request, *args, **kwargs):
        page_name = kwargs.get('page')
        content_obj = self.get_object(page_name=page_name)
        return (
            Response(
                {'title': content_obj.title, 'content': content_obj.content},
                status=status.HTTP_200_OK,
            )
            if content_obj
            else Response(constants.CONTENT_NOT_FOUND, status=status.HTTP_200_OK)
        )

    def create(self, request, *args, **kwargs):
        data = request.data
        page_name = kwargs.get('page')
        if not ContentManagement.objects.filter(type=page_name).exists():
            content_obj = ContentManagement.objects.create(title=data.get('title'),
                                                           content=data.get('content'),
                                                           type=page_name)
        else:
            content_obj = ContentManagement.objects.get(type__exact=page_name)
            content_obj.title = data.get('title')
            content_obj.content = data.get('content')
            content_obj.save(update_fields=['title', 'content'])

        return Response({'title': content_obj.title, 'content': content_obj.content}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data
        content_obj = self.get_object(page_name=kwargs.get('page'))
        if not content_obj:
            return Response(constants.CONTENT_NOT_FOUND, status=status.HTTP_200_OK)

        content_obj.title = data.get('title')
        content_obj.content = data.get('content')
        content_obj.save(update_fields=['title', 'content'])

        return Response({'title': content_obj.title, 'content': content_obj.content}, status=status.HTTP_200_OK)


class MeetTheTeamViewSet(viewsets.ModelViewSet):
    """
    Meet the team page api for dynamic content.
    CRUD operations
    """
    serializer_class = MeetTheTeamSerializer
    pagination_class = None

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsAdmin] if self.action in ['post', 'put', 'delete'] else []
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        return MeetTheTeam.objects.all().order_by('-id')





