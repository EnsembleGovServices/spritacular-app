from django.urls import path
from .views import (UploadObservationViewSet, CategoryViewSet, ObservationCommentViewSet,
                    ObservationLikeViewSet, ObservationWatchCountViewSet, ObservationGalleryViewSet,
                    ObservationVoteViewSet, ObservationVerifyViewSet, ObservationDashboardViewSet, HomeViewSet,
                    GenerateObservationCSVViewSet, ObservationImageCheck, ObservationPushBackViewSet)

urlpatterns = [
    # EXIF data from image.
    # path('metadata/', ImageMetadataViewSet.as_view(), name="get_metadata"),
    # Homepage
    path('home/', HomeViewSet.as_view(), name="home"),
    # List of category
    path('get_category_list/', CategoryViewSet.as_view({'get': 'list'}), name="get_category_list"),
    # Upload observation
    path('upload_observation/', UploadObservationViewSet.as_view({'post': 'create'}), name="upload_observation"),
    path('update_observation/<int:pk>/', UploadObservationViewSet.as_view({'put': 'update'}),
         name="update_observation"),
    path('draft_delete/<int:pk>/', UploadObservationViewSet.as_view({'delete': 'destroy'}), name="draft_delete"),
    # Get observation details
    path('get_observation_details/<int:pk>/', ObservationImageCheck.as_view(), name="get_observation_details"),
    path('observation_collection/', UploadObservationViewSet.as_view({'get': 'user_observation_collection'}),
         name="user_observation_collection"),
    path('get_draft_data/<int:pk>/', UploadObservationViewSet.as_view({'get': 'retrieve'}), name="get_draft_data"),
    # Observation Comment
    path('comment/<int:pk>/', ObservationCommentViewSet.as_view({'get': 'list', 'post': 'create'}),
         name="observation_comment"),
    # Observation Like
    path('like/<int:pk>/', ObservationLikeViewSet.as_view(), name="observation_like"),
    # Observation Watch Count
    path('watch_count/<int:pk>/', ObservationWatchCountViewSet.as_view(), name="observation_watch_count"),
    # Observation Gallery
    path('gallery/', ObservationGalleryViewSet.as_view(), name="gallery"),
    # Observation Dashboard
    path('dashboard/', ObservationDashboardViewSet.as_view({'post': 'create'}), name="dashboard"),
    # Observation Vote
    path('vote/<int:pk>/', ObservationVoteViewSet.as_view(), name="observation_vote"),
    # Approve or Reject Observation
    path('verify_observation/<int:pk>/', ObservationVerifyViewSet.as_view(), name="observation_approve_reject"),
    # Generate Observation csv
    path('get_observation_csv/', GenerateObservationCSVViewSet.as_view(), name="get_observation_csv"),
    path('observation_push_back/<int:pk>/', ObservationPushBackViewSet.as_view(), name="observation_push_back")
]
