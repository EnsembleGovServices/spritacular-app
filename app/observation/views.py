import datetime
import json
import logging
import pytz
import csv

import pandas as pd
from django.db.models import Q, Prefetch, OuterRef, Exists, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from notification.signals import generate_and_send_notification_data
from .serializers import (ObservationSerializer, ObservationCommentSerializer)
from rest_framework import status, viewsets
from users.serializers import CameraSettingSerializer
from users.permissions import IsAdminOrTrained, IsAdmin, IsObjectOwnerOrAdmin
from .models import (Observation, Category, ObservationComment, ObservationLike, ObservationWatchCount,
                     VerifyObservation, ObservationReasonForReject, ObservationImageMapping, ObservationCategoryMapping)
from users.models import CameraSetting, User
from constants import NOT_FOUND, OBS_FORM_SUCCESS, SOMETHING_WENT_WRONG, OBS_DRAFT_DELETE
from rest_framework.pagination import PageNumberPagination, CursorPagination
from sentry_sdk import capture_exception

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class CustomCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-id'


# class ImageMetadataViewSet(APIView):
#     serializer_class = ImageMetadataSerializer
#
#     def post(self, request, *args, **kwargs):
#         serializer = self.serializer_class(data=request.data)
#         if serializer.is_valid(raise_exception=True):
#             response_data = serializer.get_exif_data(serializer.validated_data)
#             return Response(json.loads(json.dumps(str(response_data))), status=status.HTTP_200_OK)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    Category list api for getting all category name and id.
    """
    queryset = Category.objects.all()

    def list(self, request, *args, **kwargs):
        data = []
        for tle in self.queryset:
            category_details = {
                'id': tle.pk,
                'name': tle.title
            }
            data.append(category_details)

        return Response(data, status=status.HTTP_200_OK)


class HomeViewSet(ListAPIView):
    """
    Homepage api
    for getting latest 4 verified observation,
    volunteers, observation count,
    country count where observation are captured.
    """
    serializer_class = ObservationSerializer

    def get_queryset(self):
        return Observation.objects.filter(is_submit=True, is_verified=True) \
                   .exclude(Q(observationimagemapping__image=None) |
                            Q(observationimagemapping__image='') |
                            Q(observationimagemapping__compressed_image=None) |
                            Q(observationimagemapping__compressed_image='')) \
                   .order_by('-pk').distinct('id') \
                   .prefetch_related('user', 'camera',
                                     Prefetch('observationimagemapping_set',
                                              queryset=ObservationImageMapping.objects.all()
                                              .order_by('pk'))
                                     ,
                                     Prefetch('observationcategorymapping_set',
                                              queryset=ObservationCategoryMapping.objects
                                              .prefetch_related('category'))
                                     ,
                                     Prefetch('observationlike_set',
                                              queryset=ObservationLike.objects.all())
                                     ,
                                     Prefetch('observationwatchcount_set',
                                              queryset=ObservationWatchCount.objects.all())
                                     )[:4]

    def get(self, request, *args, **kwargs):
        # latest_observation = Observation.objects.filter(is_verified=True,
        #                                                 observationimagemapping__image__isnull=False,
        #                                                 observationimagemapping__compressed_image__isnull=False
        #                                                 ).order_by('-pk').distinct('pk')[:4]

        if request.user.is_authenticated:
            # For normal users
            is_like = ObservationLike.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_watch = ObservationWatchCount.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_voted = VerifyObservation.objects.filter(observation=OuterRef('pk'), user=request.user)

            latest_observation = self.get_queryset().annotate(is_like=Exists(is_like),
                                                              is_watch=Exists(is_watch),
                                                              is_voted=Exists(is_voted))

        else:
            latest_observation = self.get_queryset()

        observation_counts = Observation.objects.filter(is_submit=True, is_verified=True).aggregate(
            self_count=Count('pk', distinct=True),
            country_count=Count('observationimagemapping__country_code', distinct=True),
        )
        user_count = User.objects.count()

        # observation_count = Observation.objects.filter().count()
        # observation_country_count = Observation.objects.distinct('observationimagemapping__country_code')
        # observation_user_count = Observation.objects.filter().distinct('user_id').count()

        serializer = self.serializer_class(latest_observation, many=True,
                                           context={'user_observation_collection': True, 'request': request})

        return Response({'data': {'latest_observation': serializer.data,
                                  'observation_count': observation_counts['self_count'],
                                  'observation_country_count': observation_counts['country_count'],
                                  'observation_user_count': user_count}},
                        status=status.HTTP_200_OK)


class UploadObservationViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for observations
    create, update, retrieve and user created observations.
    """
    serializer_class = ObservationSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated, IsObjectOwnerOrAdmin] if self.action in ['destroy', 'retrieve',
                                                                                        'update'] else [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        data = json.loads(request.data['data'])

        for i in request.FILES:
            data['map_data'][int(i.split('_')[-1])]['image'] = request.FILES[i]

        camera_data = data.pop('camera')

        obs_context = {'request': request, 'observation_settings': True}
        if 'is_draft' in data:
            # Adding is_draft for eliminating validations check.
            obs_context['is_draft'] = True

        # if isinstance(camera_data, dict):
        camera_serializer = CameraSettingSerializer(data=camera_data, context=obs_context)

        obs_context['camera_data'] = camera_data

        observation_serializer = self.serializer_class(data=data, context=obs_context)
        if observation_serializer.is_valid(raise_exception=True) and camera_serializer.is_valid(
                raise_exception=True):
            observation_serializer.save()
            return Response(OBS_FORM_SUCCESS, status=status.HTTP_201_CREATED)

        return Response({'observation_errors': observation_serializer.errors,
                         'camera_errors': camera_serializer.errors, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            obs_obj = Observation.objects.get(pk=kwargs.get('pk'), user=request.user, is_submit=False)
        except Observation.DoesNotExist as e:
            capture_exception(e)
            return Response(NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        data = json.loads(request.data['data'])

        for file in request.FILES:
            data['map_data'][int(file.split('_')[-1])]['image'] = request.FILES[file]

        camera_data = data.pop('camera')

        obs_context = {'request': request, 'observation_settings': True}
        if 'is_draft' in data:
            # Adding is_draft for eliminating validations check.
            obs_context['is_draft'] = True

        camera_serializer = CameraSettingSerializer(instance=obs_obj.camera, data=camera_data, context=obs_context)
        observation_serializer = self.serializer_class(instance=obs_obj, data=data, context=obs_context)

        if observation_serializer.is_valid(raise_exception=True) and camera_serializer.is_valid(raise_exception=True):
            obs_obj = observation_serializer.save()
            camera_obj = camera_serializer.save()
            obs_obj.camera = camera_obj
            obs_obj.save()
            return Response(OBS_FORM_SUCCESS, status=status.HTTP_200_OK)

        return Response({'observation_errors': observation_serializer.errors,
                         'camera_errors': camera_serializer.errors, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            # obs_obj = Observation.objects.get(pk=kwargs.get('pk'), user=request.user, is_submit=False)
            is_like = ObservationLike.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_watch = ObservationWatchCount.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_voted = VerifyObservation.objects.filter(observation=OuterRef('pk'), user=request.user)

            obs_obj = Observation.objects.filter(pk=kwargs.get('pk'), user=request.user, is_submit=False) \
                .prefetch_related('user', 'camera',
                                  Prefetch('observationimagemapping_set',
                                           queryset=ObservationImageMapping.objects.all().order_by('pk'))
                                  ,
                                  Prefetch('observationcategorymapping_set',
                                           queryset=ObservationCategoryMapping.objects.prefetch_related('category'))
                                  ,
                                  Prefetch('observationlike_set',
                                           queryset=ObservationLike.objects.all())
                                  ,
                                  Prefetch('observationwatchcount_set',
                                           queryset=ObservationWatchCount.objects.all())
                                  ).annotate(is_like=Exists(is_like),
                                             is_watch=Exists(is_watch),
                                             is_voted=Exists(is_voted)
                                             ).first()

            if not obs_obj:
                raise Observation.DoesNotExist("Not found.")
        except Observation.DoesNotExist as e:
            capture_exception(e)
            return Response(NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(obs_obj, context={'user_observation_collection': True, 'request': request})

        return Response({'data': serializer.data, 'status': 1}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        observation_obj = get_object_or_404(Observation, pk=kwargs.get('pk'), is_submit=False)
        self.check_object_permissions(request, observation_obj)
        CameraSetting.objects.filter(id=observation_obj.camera.id).delete()
        observation_obj.delete()

        return Response(OBS_DRAFT_DELETE, status=status.HTTP_200_OK)

    def user_observation_collection(self, request, *args, **kwargs):
        data = request.query_params
        filters = Q(user=request.user)
        if data.get('type') == 'verified':
            filters = filters & Q(is_submit=True, is_verified=True)
        elif data.get('type') == 'unverified':
            filters = filters & Q(is_submit=True, is_verified=False, is_reject=False)
        elif data.get('type') == 'denied':
            filters = filters & Q(is_submit=True, is_reject=True)
        elif data.get('type') == 'draft':
            filters = filters & Q(is_submit=False)

        verified_count = Observation.objects.filter(user=request.user, is_verified=True, is_submit=True).count()
        unverified_count = Observation.objects.filter(user=request.user, is_verified=False, is_submit=True,
                                                      is_reject=False).count()
        denied_count = Observation.objects.filter(user=request.user, is_reject=True, is_submit=True).count()
        draft_count = Observation.objects.filter(user=request.user, is_submit=False).count()

        # observation_filter = Observation.objects.filter(filters).order_by('-pk')

        is_like = ObservationLike.objects.filter(observation=OuterRef('pk'), user=request.user)
        is_watch = ObservationWatchCount.objects.filter(observation=OuterRef('pk'), user=request.user)
        is_voted = VerifyObservation.objects.filter(observation=OuterRef('pk'), user=request.user)
        observation_filter = Observation.objects.filter(filters) \
            .order_by('-pk').distinct('id') \
            .prefetch_related('user', 'camera',
                              Prefetch('observationimagemapping_set',
                                       queryset=ObservationImageMapping.objects.all().order_by('pk'))
                              ,
                              Prefetch('observationcategorymapping_set',
                                       queryset=ObservationCategoryMapping.objects.prefetch_related('category'))
                              ,
                              Prefetch('observationlike_set',
                                       queryset=ObservationLike.objects.all())
                              ,
                              Prefetch('observationwatchcount_set',
                                       queryset=ObservationWatchCount.objects.all())
                              ).annotate(is_like=Exists(is_like),
                                         is_watch=Exists(is_watch),
                                         is_voted=Exists(is_voted)
                                         )

        page = self.paginate_queryset(observation_filter)
        if not page:
            serializer = self.serializer_class(observation_filter, many=True,
                                               context={'user_observation_collection': True, 'request': request})

            return Response({'results': {'data': serializer.data, 'verified_count': verified_count,
                                         'unverified_count': unverified_count, 'denied_count': denied_count,
                                         'draft_count': draft_count}}, status=status.HTTP_200_OK)
        else:
            serializer = self.serializer_class(page, many=True,
                                               context={'user_observation_collection': True, 'request': request})

            return self.get_paginated_response({'data': serializer.data, 'verified_count': verified_count,
                                                'unverified_count': unverified_count, 'denied_count': denied_count,
                                                'draft_count': draft_count})


class ObservationImageCheck(APIView):
    """
    Observation image check api for checking of the image processing is done or not.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            obs_obj = Observation.objects.get(pk=kwargs.get('pk'))
        except Observation.DoesNotExist as e:
            capture_exception(e)
            return Response(NOT_FOUND, status=status.HTTP_404_NOT_FOUND)

        image_data = []
        for im in ObservationImageMapping.objects.filter(observation=obs_obj).order_by('pk'):
            image_data.append(im.image.url if im.image else None)

        return Response({'data': image_data, 'status': 1}, status=status.HTTP_200_OK)


class ObservationCommentViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for observation comments
    """
    serializer_class = ObservationCommentSerializer

    def get_permissions(self):
        permission_classes = (IsAuthenticated,) if self.action == 'post' else []
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        observation = get_object_or_404(Observation, pk=kwargs.get('pk'))
        observation_comment_obj = ObservationComment.objects.filter(observation=observation)
        serializer = self.serializer_class(observation_comment_obj, many=True)
        return Response({'data': serializer.data, 'status': 1}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        data = request.data
        get_object_or_404(Observation, pk=kwargs.get('pk'))
        data['observation'] = kwargs.get('pk')
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({'data': serializer.data, 'status': 1}, status=status.HTTP_201_CREATED)

        return Response({'detail': serializer.errors, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)


class ObservationLikeViewSet(APIView):
    """
    observation like api.
    storing users and observation mapping for like count.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        get_object_or_404(Observation, pk=kwargs.get('pk'))
        data = request.data
        if data.get('is_like') == '1':
            if ObservationLike.objects.filter(observation_id=kwargs.get('pk'), user=request.user).exists():
                like_count = ObservationLike.objects.filter(observation_id=kwargs.get('pk')).count()
                return Response({'like_count': like_count, 'status': 0}, status=status.HTTP_400_BAD_REQUEST)

            ObservationLike.objects.create(observation_id=kwargs.get('pk'), user=request.user)
            like_status = True
        else:
            # Observation Dislike
            ObservationLike.objects.filter(observation_id=kwargs.get('pk'), user=request.user).delete()
            like_status = False

        like_count = ObservationLike.objects.filter(observation_id=kwargs.get('pk')).count()
        return Response({'like_count': like_count, 'status': 1, 'like': like_status}, status=status.HTTP_200_OK)


class ObservationWatchCountViewSet(APIView):
    """
    observation watch count api
    storing user observation mapping for watch count.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        get_object_or_404(Observation, pk=kwargs.get('pk'))
        if not ObservationWatchCount.objects.filter(observation_id=kwargs.get('pk'), user=request.user).exists():
            ObservationWatchCount.objects.create(observation_id=kwargs.get('pk'), user=request.user)

        watch_count = ObservationWatchCount.objects.filter(observation_id=kwargs.get('pk')).count()

        return Response({'watch_count': watch_count, 'status': 1}, status=status.HTTP_200_OK)


class ObservationGalleryViewSet(ListAPIView):
    """
    Observation gallery page api with paginated response.
    """
    pagination_class = CustomCursorPagination

    def get_queryset(self, *args):
        return Observation.objects.all() \
            .exclude(Q(observationimagemapping__image=None) | Q(observationimagemapping__image='')) \
            .order_by('-pk').distinct('id') \
            .prefetch_related('user', 'camera',
                              Prefetch('observationimagemapping_set',
                                       queryset=ObservationImageMapping.objects.all().order_by('pk'))
                              ,
                              Prefetch('observationcategorymapping_set',
                                       queryset=ObservationCategoryMapping.objects.prefetch_related('category'))
                              ,
                              Prefetch('observationlike_set',
                                       queryset=ObservationLike.objects.all())
                              ,
                              Prefetch('observationwatchcount_set',
                                       queryset=ObservationWatchCount.objects.all())
                              )

    def get(self, request, *args, **kwargs):
        data = request.query_params

        # Storing gallery filters
        filters = Q(is_submit=True, is_reject=False)
        if data.get('country'):
            filters = filters & Q(observationimagemapping__country_code__iexact=data.get('country'))
        if data.get('category'):
            filters = filters & Q(observationcategorymapping__category__title__iexact=data.get('category'))
        if data.get('status') == 'verified':
            filters = filters & Q(is_verified=True)
        if data.get('status') == 'unverified':
            filters = filters & Q(is_verified=False, is_reject=False)

        if request.user.is_authenticated and (request.user.is_trained or request.user.is_superuser):
            # Trained user can see both verified and unverified observation on gallery screen.
            is_like = ObservationLike.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_watch = ObservationWatchCount.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_voted = VerifyObservation.objects.filter(observation=OuterRef('pk'), user=request.user)

            observation_filter = self.get_queryset().filter(filters).annotate(is_like=Exists(is_like),
                                                                              is_watch=Exists(is_watch),
                                                                              is_voted=Exists(is_voted)
                                                                              )

        elif request.user.is_authenticated:
            # For normal users
            is_like = ObservationLike.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_watch = ObservationWatchCount.objects.filter(observation=OuterRef('pk'), user=request.user)
            is_voted = VerifyObservation.objects.filter(observation=OuterRef('pk'), user=request.user)

            observation_filter = self.get_queryset().filter(is_submit=True, is_verified=True).annotate(
                is_like=Exists(is_like),
                is_watch=Exists(is_watch),
                is_voted=Exists(is_voted)
            )

        else:
            # For unauthenticated users
            observation_filter = self.get_queryset().filter(is_submit=True, is_verified=True)

        page = self.paginate_queryset(observation_filter)
        if not page:
            serializer = ObservationSerializer(observation_filter, many=True,
                                               context={'user_observation_collection': True, 'request': request})
            return Response({'results': {'data': serializer.data, 'status': 1}}, status=status.HTTP_200_OK)

        else:
            serializer = ObservationSerializer(page, many=True, context={'user_observation_collection': True,
                                                                         'request': request})
            return self.get_paginated_response({'data': serializer.data})


class ObservationVoteViewSet(APIView):
    """
    Observation vote api.
    Allowed for admin and trained users.
    """
    permission_classes = (IsAuthenticated, IsAdminOrTrained)

    def post(self, request, *args, **kwargs):
        observation_obj = get_object_or_404(Observation, pk=kwargs.get('pk'))
        data = request.data
        # Check if the user is not voting his/her created observation
        self.check_object_permissions(request, observation_obj)

        is_status_change = False
        if VerifyObservation.objects.filter(observation=observation_obj, user=request.user).exists():
            # If user have already voted atleast one TLE of the observation
            return Response({'success': 'You have already voted for this observation.', 'status': 1},
                            status=status.HTTP_200_OK)

        for user_vote in data.get('votes'):
            if ObservationCategoryMapping.objects.filter(observation=observation_obj,
                                                         category_id=user_vote.get("category_id")).exists():
                # If the observation have the TLE mapping
                verify_obs_obj = VerifyObservation.objects.create(observation=observation_obj, user=request.user,
                                                                  category_id=user_vote.get("category_id"),
                                                                  vote=user_vote.get("vote"))

                if verify_obs_obj.user.is_superuser and verify_obs_obj.vote:
                    # If an admin votes yes on any category of the observation it will send for verification.
                    is_status_change = True

                if VerifyObservation.objects.filter(observation=observation_obj,
                                                    category_id=user_vote.get("category_id"), vote=True).count() > 3:
                    # If any category of the observation have more than 3 yes votes it will send for verification.
                    is_status_change = True

        if is_status_change:
            # Set is_to_be_verify flag to True.
            observation_obj.is_verified = True
            observation_obj.save(update_fields=['is_verified'])
            # Send notification after observation approved
            generate_and_send_notification_data("Observation Approved", "Your observation is approved.",
                                                observation_obj.user, request.user, observation_obj, 'verified')

        return Response({'success': 'Successfully Voted.', 'status': 1, 'is_verified': is_status_change},
                        status=status.HTTP_200_OK)


class ObservationVerifyViewSet(APIView):
    """
    observation approve and reject api.
    Allowed to admin users only.
    """
    permission_classes = (IsAuthenticated, IsAdmin)

    def post(self, request, *args, **kwargs):
        observation_obj = get_object_or_404(Observation, pk=kwargs.get('pk'))
        data = request.data

        if data.get('name') == "APPROVE" and not observation_obj.is_verified:
            # Approved
            observation_obj.is_verified = True
            observation_obj.is_reject = False
            observation_obj.verified_by = request.user
            observation_obj.save(update_fields=['is_verified', 'is_reject', 'verified_by'])

            # Send notification after observation approved
            generate_and_send_notification_data("Observation Approved", "Your observation is approved.",
                                                observation_obj.user, request.user, observation_obj, 'verified')

            return Response({'success': 'Observation Approved.'}, status=status.HTTP_200_OK)

        elif data.get('name') == "REJECT" and not observation_obj.is_reject:
            # Reject
            reason_for_reject = None
            observation_obj.is_reject = True
            observation_obj.is_verified = False
            observation_obj.verified_by = request.user
            observation_obj.save(update_fields=['is_reject', 'is_verified', 'verified_by'])

            if data.get('reason'):
                reason_data = data.get('reason')
                # Reason for reject
                ObservationReasonForReject.objects.create(observation=observation_obj,
                                                          inappropriate_image=reason_data.get('inappropriate_image'),
                                                          other=reason_data.get('other'),
                                                          additional_comment=reason_data.get('additional_comment',
                                                                                             None))
                reason_for_reject = reason_data.get('additional_comment', None)
            # Send notification after observation rejected
            generate_and_send_notification_data("Observation Rejected",
                                                reason_for_reject or "Your observation is rejected.",
                                                observation_obj.user, request.user, observation_obj, 'denied')

            return Response({'success': 'Observation Rejected.'}, status=status.HTTP_200_OK)

        return Response(SOMETHING_WENT_WRONG, status=status.HTTP_400_BAD_REQUEST)


class ObservationDashboardViewSet(viewsets.ModelViewSet):
    """
    observation dashboard api.
    accessible by admin only, for approving and rejecting observations.
    """
    permission_classes = (IsAuthenticated, IsAdmin)
    serializer_class = ObservationSerializer
    pagination_class = CustomCursorPagination
    queryset = Observation.objects.all()

    def create(self, request, *args, **kwargs):
        query_data = request.query_params
        data = request.data

        filters = Q(is_submit=True)
        if data.get('from_obs_data'):
            date_time_obj = pytz.utc.localize(datetime.datetime.strptime(data.get('from_obs_data'), "%d/%m/%Y %H:%M"))
            filters = filters & Q(observationimagemapping__obs_date_time_as_per_utc__gte=date_time_obj)
        if data.get('to_obs_data'):
            date_time_obj = pytz.utc.localize(datetime.datetime.strptime(data.get('to_obs_data'), "%d/%m/%Y %H:%M"))
            filters = filters & Q(observationimagemapping__obs_date_time_as_per_utc__lte=date_time_obj)
        if query_data.get('country'):
            filters = filters & Q(observationimagemapping__country_code__iexact=query_data.get('country'))
        if query_data.get('status') == 'verified':
            filters = filters & Q(is_verified=True)
        if query_data.get('status') == 'unverified':
            filters = filters & Q(is_verified=False, is_reject=False)
        if query_data.get('category'):
            filters = filters & Q(observationcategorymapping__category__title__iexact=query_data.get('category'))

        is_like = ObservationLike.objects.filter(observation=OuterRef('pk'), user=request.user)
        is_watch = ObservationWatchCount.objects.filter(observation=OuterRef('pk'), user=request.user)
        is_voted = VerifyObservation.objects.filter(observation=OuterRef('pk'), user=request.user)

        observation_filter = Observation.objects.filter(filters). \
            exclude(Q(observationimagemapping__image=None) | Q(observationimagemapping__image='')).order_by('-pk') \
            .prefetch_related('user', 'camera',
                              Prefetch('observationimagemapping_set',
                                       queryset=ObservationImageMapping.objects.all().order_by('pk'))
                              ,
                              Prefetch('observationcategorymapping_set',
                                       queryset=ObservationCategoryMapping.objects.prefetch_related('category'))
                              ,
                              Prefetch('observationlike_set',
                                       queryset=ObservationLike.objects.all())
                              ,
                              Prefetch('observationwatchcount_set',
                                       queryset=ObservationWatchCount.objects.all())
                              ).annotate(is_like=Exists(is_like),
                                         is_watch=Exists(is_watch),
                                         is_voted=Exists(is_voted)
                                         )

        page = self.paginate_queryset(observation_filter)
        if not page:
            serializer = self.serializer_class(observation_filter, many=True,
                                               context={'user_observation_collection': True, 'request': request})
            return Response({'results': {'data': serializer.data, 'status': 1}}, status=status.HTTP_200_OK)

        else:
            serializer = self.serializer_class(page, many=True, context={'user_observation_collection': True,
                                                                         'request': request})
            return self.get_paginated_response({'data': serializer.data})


# class GenerateObservationCSVViewSet(APIView):
#     """
#     Generate observation data in csv api old way.
#     storing all selected observation data in csv file.
#     """
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request, *args, **kwargs):
#         observation_list = request.data.get('observation_ids', [])
#         observation_filter = Observation.objects.filter(id__in=observation_list)
#
#         # fields for dataframe
#         q = observation_filter.values('id',
#                                       'user__first_name',
#                                       'user__last_name',
#                                       'observationimagemapping__country_code',
#                                       'observationimagemapping__location',
#                                       'observationimagemapping__latitude',
#                                       'observationimagemapping__longitude',
#                                       'observationimagemapping__obs_date_time_as_per_utc',
#                                       'observationimagemapping__time_accuracy',
#                                       'observationimagemapping__is_precise_azimuth',
#                                       'observationimagemapping__azimuth',
#                                       'observationimagemapping__timezone',
#                                       'camera__camera_type',
#                                       'camera__focal_length',
#                                       'camera__aperture',
#                                       'camera__iso',
#                                       'camera__shutter_speed',
#                                       'camera__fps',
#                                       'camera__question_field_one',
#                                       'camera__question_field_two',
#                                       'elevation_angle',
#                                       'video_url',
#                                       'story',
#                                       'media_file_url',
#                                       'is_submit',
#                                       'is_verified',
#                                       'is_reject').distinct('id')
#
#         # converting queryset into dataframe
#         df = pd.DataFrame.from_records(q)
#
#         # renaming column for csv file
#         df.columns = ['id', 'first_name', 'last_name', 'country_code',
#                       'location', 'latitude', 'longitude', 'obs_date_time_as_per_utc',
#                       'time_accuracy', 'is_precise_azimuth', 'azimuth', 'timezone',
#                       'camera_type', 'focal_length', 'aperture', 'iso', 'shutter_speed', 'fps',
#                       'track_of_time', 'special_equipment_used', 'elevation_angle', 'video_url', 'story',
#                       'media_file_url', 'is_submit', 'is_verified', 'is_reject']
#
#         # csv file generation
#         response = HttpResponse(content_type='text/csv', status=status.HTTP_200_OK)
#         response['Content-Disposition'] = 'attachment; filename=observation_data.csv'
#         df.to_csv(path_or_buf=response, index=False)
#
#         return response


class GenerateObservationCSVViewSet(APIView):
    """
    Generate observation data in csv api new way.
    storing all selected observation data in csv file.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        observation_list = request.data.get('observation_ids', [])
        observation_filter = ObservationImageMapping.objects.filter(
            observation__id__in=observation_list
        ).select_related('observation', 'observation__user', 'observation__camera')

        response = HttpResponse(
            content_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename="observation_data.csv"'},
        )

        writer = csv.writer(response)
        writer.writerow(['id', 'first_name', 'last_name', 'country_code',
                         'location', 'latitude', 'longitude', 'obs_date_time_as_per_utc',
                         'time_accuracy', 'is_precise_azimuth', 'azimuth', 'timezone',
                         'camera_type', 'focal_length', 'aperture', 'iso', 'shutter_speed', 'fps',
                         'track_of_time', 'special_equipment_used', 'elevation_angle', 'video_url', 'story',
                         'media_file_url', 'is_submit', 'is_verified', 'is_reject', 'image_url'])

        for observation_obj in observation_filter:
            writer.writerow([
                observation_obj.observation_id,
                observation_obj.observation.user.first_name,
                observation_obj.observation.user.last_name,
                observation_obj.country_code,
                observation_obj.location,
                observation_obj.latitude,
                observation_obj.longitude,
                observation_obj.obs_date_time_as_per_utc,
                observation_obj.time_accuracy,
                observation_obj.is_precise_azimuth,
                observation_obj.azimuth,
                observation_obj.timezone,
                observation_obj.observation.camera.camera_type,
                observation_obj.observation.camera.focal_length,
                observation_obj.observation.camera.aperture,
                observation_obj.observation.camera.iso,
                observation_obj.observation.camera.shutter_speed,
                observation_obj.observation.camera.fps,
                observation_obj.observation.camera.question_field_one,
                observation_obj.observation.camera.question_field_two,
                observation_obj.observation.elevation_angle,
                observation_obj.observation.video_url,
                observation_obj.observation.story,
                observation_obj.observation.media_file_url,
                observation_obj.observation.is_submit,
                observation_obj.observation.is_verified,
                observation_obj.observation.is_reject,
                observation_obj.image.url,
             ])

        return response
