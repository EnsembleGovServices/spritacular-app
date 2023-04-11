from django.core.validators import FileExtensionValidator
from rest_framework import serializers
from .models import (ObservationImageMapping, Observation, Category, ObservationCategoryMapping, ObservationComment)
from users.models import CameraSetting
from users.serializers import UserRegisterSerializer, CameraSettingSerializer
from constants import FIELD_REQUIRED, SINGLE_IMAGE_VALID, MULTIPLE_IMAGE_VALID
from observation.tasks import get_original_image
from spritacular.utils import compress_and_save_image_locally


# class ImageMetadataSerializer(serializers.Serializer):
#     image = serializers.ImageField(validators=[FileExtensionValidator(['jpg', 'tiff', 'png', 'jpeg'])])
#
#     def get_exif_data(self, validated_data):
#         # img = Image(validated_data.get('image'))
#         # print(f"Latitude: {img.gps_latitude} {img.gps_latitude_ref}")
#         # print(f"Longitude: {img.gps_longitude} {img.gps_longitude_ref}\n")
#
#         exif = {}
#         gps = {}
#         latitude = None
#         longitude = None
#         try:
#             image = validated_data.get('image')
#             img = Image.open(image)
#             if img._getexif():
#                 for tag, value in img._getexif().items():
#                     if tag in TAGS:
#                         exif[TAGS[tag]] = value
#
#             trash_data = ['MakerNote', 'UserComment', 'ImageDescription']
#
#             for i in trash_data:
#                 if i in exif:
#                     exif.pop(i)
#
#             print(exif)
#
#             if 'GPSInfo' in exif:
#                 for key, val in exif['GPSInfo'].items():
#                     name = GPSTAGS.get(key, key)
#                     print(f"{name}: {exif['GPSInfo'][key]}")
#                     gps[name] = val
#
#                 if gps.get('GPSLatitude') and gps.get('GPSLatitudeRef'):
#                     latitude = dms_coordinates_to_dd_coordinates(gps['GPSLatitude'], gps['GPSLatitudeRef'])
#                     print(
#                         f"Latitude (DD): {dms_coordinates_to_dd_coordinates(gps['GPSLatitude'], gps['GPSLatitudeRef'])}")
#
#                 if gps.get('GPSLongitude') and gps.get('GPSLongitudeRef'):
#                     longitude = dms_coordinates_to_dd_coordinates(gps['GPSLongitude'], gps['GPSLongitudeRef'])
#                     print(
#                         f"Longitude (DD): {dms_coordinates_to_dd_coordinates(gps['GPSLongitude'], gps['GPSLongitudeRef'])}\n")
#
#         except Exception as e:
#             print(f"---{e}")
#
#         return {"latitude": latitude, "longitude": longitude, "FocalLength": exif.get('FocalLength'),
#                 "DateTime": exif.get('DateTime'), "ISOSpeedRatings": exif.get('ISOSpeedRatings'),
#                 "ApertureValue": exif.get('ApertureValue')}


class ObservationCategorySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True, required=False,
                                                  allow_null=True)
    is_other = serializers.BooleanField(default=False)
    custom_category = serializers.CharField(required=False)

    class Meta:
        model = ObservationCategoryMapping
        fields = ('category', 'is_other', 'custom_category')


class ObservationImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(validators=[FileExtensionValidator(['jpg', 'png', 'jpeg'])], required=True)
    category_map = ObservationCategorySerializer(required=False)
    # latitude = serializers.DecimalField(coerce_to_string=False, max_digits=22, decimal_places=16, allow_null=True)
    # longitude = serializers.DecimalField(coerce_to_string=False, max_digits=22, decimal_places=16, allow_null=True)

    class Meta:
        model = ObservationImageMapping
        fields = ('id', 'image', 'location', 'place_uid', 'country_code', 'latitude', 'longitude', 'obs_date', 'obs_time',
                  'timezone', 'azimuth', 'category_map', 'obs_date_time_as_per_utc', 'time_accuracy',
                  'is_precise_azimuth', 'compressed_image', 'image_name')


class ObservationSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    map_data = ObservationImageSerializer(many=True, write_only=True)
    # camera = serializers.PrimaryKeyRelatedField(queryset=CameraSetting.objects.all(), allow_null=True, required=False)
    images = serializers.SerializerMethodField('get_image', read_only=True)
    user_data = serializers.SerializerMethodField('get_user', read_only=True)
    category_data = serializers.SerializerMethodField('get_category_name', read_only=True)
    camera_data = serializers.SerializerMethodField('get_camera', read_only=True)
    like_watch_count_data = serializers.SerializerMethodField('get_like_watch_count_data', read_only=True)

    class Meta:
        model = Observation
        fields = ('id', 'user', 'image_type', 'map_data', 'elevation_angle', 'video_url', 'story', 'images',
                  'user_data', 'is_verified', 'category_data', 'camera_data', 'like_watch_count_data', 'is_submit',
                  'is_reject', 'active_tab', 'media_file_url')

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     if 'user_observation_collection' in self.context:
    #         del self.fields['map_data']
    #         del self.fields['camera']

    def get_image(self, data):
        obj = data.observationimagemapping_set.all()
        serialize_data = ObservationImageSerializer(obj, many=True).data
        for image_map_obj in serialize_data:
            image_map_obj['category_map'] = {}
            image_map_obj['category_map']['category'] = [
                type_id.category.id for type_id in data.observationcategorymapping_set.all()]
        return serialize_data

    def get_user(self, data):
        user = data.user
        serializer = UserRegisterSerializer(user).data
        serializer['is_voted'] = False
        serializer['is_can_vote'] = False
        if self.context.get('request').user.is_authenticated:
            serializer['is_voted'] = data.is_voted
            serializer['is_can_vote'] = user != self.context.get('request').user
        return serializer

    def get_category_name(self, data):
        obj = data.observationcategorymapping_set.all()
        return [{"name": i.category.title, "id": i.category.id} for i in obj]

    def get_camera(self, data):
        return CameraSettingSerializer(data.camera).data

    def get_like_watch_count_data(self, data):
        like_count = data.observationlike_set.count()
        watch_count = data.observationwatchcount_set.count()
        is_like = None
        is_watch = None
        if self.context.get('request').user.is_authenticated:
            is_like = data.is_like
            is_watch = data.is_watch
        return {'like_count': like_count, 'is_like': is_like, 'watch_count': watch_count, 'is_watch': is_watch}

    def validate(self, data):
        image_data = data.get('map_data')
        error_field = {}
        if self.context.get('is_draft') is None:
            for obs_data in image_data:
                if obs_data.get('category_map') and not obs_data.get('category_map')['category']:
                    error_field['category'] = [FIELD_REQUIRED.format("Category")]

                elif not obs_data.get('location'):
                    error_field['location'] = [FIELD_REQUIRED.format("Location")]

                elif not obs_data.get('longitude'):
                    error_field['longitude'] = [FIELD_REQUIRED.format("Longitude")]

                elif not obs_data.get('latitude'):
                    error_field['latitude'] = [FIELD_REQUIRED.format("Latitude")]

                elif not obs_data.get('timezone'):
                    error_field['timezone'] = [FIELD_REQUIRED.format("Timezone")]

                elif not obs_data.get('obs_date'):
                    error_field['obs_date'] = [FIELD_REQUIRED.format("Observation date")]

                elif not obs_data.get('obs_time'):
                    error_field['obs_time'] = [FIELD_REQUIRED.format("Observation time")]

                elif not obs_data.get('azimuth'):
                    error_field['azimuth'] = [FIELD_REQUIRED.format("Azimuth")]

                if error_field:
                    raise serializers.ValidationError(error_field, code=400)

        return data

    def create(self, validated_data):
        image_data = validated_data.pop('map_data')
        # camera_data = self.context.get('camera_data')
        # Flag for submit or draft request
        submit_flag = self.context.get('is_draft') is None
        observation = None

        self.validate_image_length(validated_data, image_data)

        for data in image_data:
            observation = Observation.objects.create(**validated_data, is_submit=submit_flag)

            if data.get('category_map'):
                category_data = data.pop('category_map')
                for tle in category_data['category']:
                    if not ObservationCategoryMapping.objects.filter(observation_id=observation.id,
                                                                     category=tle).exists():
                        ObservationCategoryMapping.objects.create(observation_id=observation.id, category=tle)

            # Image Compression
            image_file = data.pop('image')
            # newfile_name = f"{uuid.uuid4()}.{image_file.name.split('.')[-1]}"  # creating unique file name
            #
            # # First saving original file locally.
            # fs = FileSystemStorage(location="")
            # file_name = fs.save(newfile_name, image_file)
            # image_file_name = fs.url(file_name)
            #
            # compressed_image = compress_image(image_file, newfile_name)  # Compression function call

            image_file_name, compressed_image = compress_and_save_image_locally(image_file)  # Compression function call

            obs_image_map_obj = ObservationImageMapping.objects.create(**data,
                                                                       compressed_image=compressed_image,
                                                                       observation_id=observation.id,
                                                                       image_name=image_file_name)

            # obs_image_map_obj = ObservationImageMapping.objects.create(**image_data[i], observation_id=observation.id)
            if obs_image_map_obj.obs_date and obs_image_map_obj.obs_time:
                obs_image_map_obj.set_utc()
            get_original_image.delay(obs_image_map_obj.id)  # Calling celery task to save original image from local.

        return observation

    @staticmethod
    def validate_image_length(validated_data, image_data):
        if validated_data.get('image_type') == 1 and len(image_data) > 1:
            raise serializers.ValidationError(SINGLE_IMAGE_VALID, code=400)

        elif validated_data.get('image_type') in [2, 3] and len(image_data) > 3:
            raise serializers.ValidationError(MULTIPLE_IMAGE_VALID, code=400)

    @staticmethod
    def create_camera_observation(camera_data, validated_data, submit_flag):
        camera_obj = CameraSetting.objects.create(user=validated_data.get('user'),
                                                  camera_type=camera_data.get('camera_type'),
                                                  iso=camera_data.get('iso'),
                                                  shutter_speed=camera_data.get('shutter_speed'),
                                                  fps=camera_data.get('fps'),
                                                  lens_type=camera_data.get('lens_type'),
                                                  focal_length=camera_data.get('focal_length'),
                                                  aperture=camera_data.get('aperture', 'None'),
                                                  question_field_one=camera_data.get('question_field_one'),
                                                  question_field_two=camera_data.get('question_field_two'),
                                                  is_profile_camera_settings=False)

        observation = Observation.objects.create(**validated_data, is_submit=submit_flag, camera=camera_obj)

        return camera_obj, observation

    def update(self, instance, validated_data):
        image_data = validated_data.pop('map_data')
        # Flag for submit or draft request
        submit_flag = self.context.get('is_draft') is None

        if validated_data.get('image_type') in [1, 2] and len(image_data) > 1:
            raise serializers.ValidationError(SINGLE_IMAGE_VALID, code=400)

        elif validated_data.get('image_type') == 3 and len(image_data) > 3:
            raise serializers.ValidationError(MULTIPLE_IMAGE_VALID, code=400)

        # if submit
        instance.is_submit = submit_flag
        instance.elevation_angle = validated_data.get('elevation_angle')
        instance.video_url = validated_data.get('video_url')
        instance.story = validated_data.get('story')
        instance.active_tab = validated_data.get('active_tab')
        instance.media_file_url = validated_data.get('media_file_url')
        instance.save()

        category_data = image_data[0].get('category_map')
        # Deleting all previously selected tle
        ObservationCategoryMapping.objects.filter(observation=instance).delete()

        for tle in category_data.get('category'):
            ObservationCategoryMapping.objects.create(observation_id=instance.id, category=tle)

        if validated_data.get('image_type') != 3:
            obs_image_map_obj = ObservationImageMapping.objects.filter(observation=instance).order_by('pk')
            for obs_map_data in obs_image_map_obj:
                # i.image = image_data[0].get('image')

                # Image Compression
                image_file = image_data[0].get('image')
                # Compression function call
                image_file_name, compressed_image = compress_and_save_image_locally(image_file)

                obs_map_data.location = image_data[0].get('location')
                obs_map_data.timezone = image_data[0].get('timezone')
                obs_map_data.longitude = image_data[0].get('longitude')
                obs_map_data.latitude = image_data[0].get('latitude')
                obs_map_data.azimuth = image_data[0].get('azimuth')
                obs_map_data.obs_date = image_data[0].get('obs_date')
                obs_map_data.obs_time = image_data[0].get('obs_time')
                obs_map_data.is_precise_azimuth = image_data[0].get('is_precise_azimuth')
                obs_map_data.time_accuracy = image_data[0].get('time_accuracy')
                obs_map_data.image_name = image_file_name
                obs_map_data.compressed_image = compressed_image
                obs_map_data.save()
                if obs_map_data.obs_date and obs_map_data.obs_time:
                    obs_map_data.set_utc()
                get_original_image.delay(obs_map_data.id)  # Calling celery task to save original image from local.

        else:
            ObservationImageMapping.objects.filter(observation=instance).delete()
            for obs_map_data in image_data:
                obs_map_data.pop('category_map')
                obs_map_data.pop('compressed_image', None)
                obs_map_data.pop('image_name', None)

                # Image Compression
                image_file = obs_map_data.pop('image')
                # Compression function call
                image_file_name, compressed_image = compress_and_save_image_locally(image_file)
                obs_image_map_obj = ObservationImageMapping.objects.create(**obs_map_data, observation=instance,
                                                                           compressed_image=compressed_image,
                                                                           image_name=image_file_name)
                if obs_image_map_obj.obs_date and obs_image_map_obj.obs_time:
                    obs_image_map_obj.set_utc()
                get_original_image.delay(obs_image_map_obj.id)  # Calling celery task to save original image from local.

        return instance


class ObservationCommentSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    user_data = serializers.SerializerMethodField('get_user_data', read_only=True)

    class Meta:
        model = ObservationComment
        fields = '__all__'

    def get_user_data(self, data):
        user_obj = data.user
        return UserRegisterSerializer(user_obj).data

