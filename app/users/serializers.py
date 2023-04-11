import constants

from django.contrib.auth import authenticate
from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from rest_framework.validators import UniqueValidator
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password

from .models import User, CameraSetting

from sentry_sdk import capture_exception


class LoginSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        token_data = super().validate(attrs)

        data = {
            'refresh': token_data.get('refresh'),
            'access': token_data.get('access'),
            'id': self.user.id,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
            'location': self.user.location,
            'place_uid': self.user.place_uid,
            'country_code': self.user.country_code,
            'is_first_login': self.user.is_first_login,
            'profile_image': self.user.profile_image.url if self.user.profile_image else None,
            'location_metadata': self.user.location_metadata,
            'is_superuser': self.user.is_superuser,
            'is_trained': self.user.is_trained,
            'is_user': not self.user.is_superuser and not self.user.is_trained
        }

        if self.user.is_first_login:
            self.user.is_first_login = False
            self.user.save(update_fields=['is_first_login'])

        # self.user.last_login = timezone.now()
        # self.user.save(update_fields=['last_login'])

        return data


class UserRegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(validators=[UniqueValidator(
        queryset=User.objects.all(),
        message=constants.ACCOUNT_ALREADY_EXISTS,
        lookup="iexact"
    )], )
    location = serializers.CharField(required=True)
    profile_image = serializers.ImageField(required=False,
                                           validators=[FileExtensionValidator(['jpg', 'tiff', 'png', 'jpeg'])])
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    location_metadata = serializers.JSONField(allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'password', 'location', 'country_code',
                  'place_uid', 'profile_image', 'location_metadata')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'method' in self.context and self.context['method'] == 'PUT':
            del self.fields['password']

    def validate_password(self, value):
        validate_password(password=value, user=User)
        return value

    def create(self, validated_data):
        user = User.objects.create(first_name=validated_data['first_name'],
                                   last_name=validated_data['last_name'],
                                   email=validated_data['email'],
                                   location=validated_data['location'],
                                   profile_image=validated_data.get('profile_image', ''),
                                   country_code=validated_data.get('country_code'),
                                   place_uid=validated_data.get('place_uid'),
                                   is_first_login=True, location_metadata=validated_data.get('location_metadata'))
        user.set_password(validated_data.get('password'))
        user.save()

        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    # def validate_new_password(self, value):
    #     user = self.context.get('user')
    #     validate_password(password=value, user=user)
    #     return value

    def validate(self, validated_data):
        old_password = validated_data.get('old_password')
        new_password = validated_data.get('new_password')
        confirm_password = validated_data.get('confirm_password')
        user = self.context.get('user')

        user_check = authenticate(username=user.email, password=old_password)
        if user_check:
            try:
                validate_password(password=new_password, user=user)
            except Exception as e:
                capture_exception(e)
                raise serializers.ValidationError({'details': e.messages}, code=400)
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()

            else:
                raise serializers.ValidationError({'details': constants.NEW_PASS_CONFIRM_PASS_INVALID}, code=400)
        else:
            raise serializers.ValidationError({'details': constants.INVALID_OLD_PASS}, code=400)

        return validated_data


class CameraSettingSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    # camera_type = serializers.CharField(required=True)
    # focal_length = serializers.CharField(required=True)
    # aperture = serializers.CharField(required=True)

    class Meta:
        model = CameraSetting
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'observation_settings' not in self.context or 'is_draft' not in self.context:
            self.fields['camera_type'] = serializers.CharField(required=True)
            self.fields['focal_length'] = serializers.CharField(required=True)
            self.fields['aperture'] = serializers.FloatField(required=True)

    def create(self, validated_data):
        if not self.context.get('observation_settings') and CameraSetting.objects.filter(is_profile_camera_settings=True, user=validated_data.get('user')).exists():
            raise serializers.ValidationError({'details': constants.CAMERA_SETTINGS_ALREADY_EXISTS}, code=400)
        camera_type = validated_data.get('camera_type')
        iso = validated_data.get('iso')
        shutter_speed = validated_data.get('shutter_speed')
        fps = validated_data.get('fps')
        lens_type = validated_data.get('lens_type')
        focal_length = validated_data.get('focal_length')
        aperture = validated_data.get('aperture', None)
        question_field_one = validated_data.get('question_field_one')
        question_field_two = validated_data.get('question_field_two')
        user = validated_data.get('user')

        camera_setting = CameraSetting.objects.create(camera_type=camera_type, iso=iso, shutter_speed=shutter_speed,
                                                      fps=fps, lens_type=lens_type, focal_length=focal_length,
                                                      aperture=aperture, question_field_one=question_field_one,
                                                      question_field_two=question_field_two, user=user)

        if self.context.get('observation_settings'):
            # For differentiating camera settings in profile and settings used in observations upload form.
            camera_setting.is_profile_camera_settings = False
            camera_setting.save(update_fields=['is_profile_camera_settings'])

        return camera_setting

    def update(self, instance, validated_data):
        camera_type = validated_data.get('camera_type')
        iso = validated_data.get('iso')
        shutter_speed = validated_data.get('shutter_speed')
        fps = validated_data.get('fps')
        lens_type = validated_data.get('lens_type')
        focal_length = validated_data.get('focal_length')
        aperture = validated_data.get('aperture', None)
        question_field_one = validated_data.get('question_field_one')
        question_field_two = validated_data.get('question_field_two')
        user = validated_data.get('user')

        instance.camera_type = camera_type
        instance.iso = iso
        instance.shutter_speed = shutter_speed
        instance.fps = fps
        instance.lens_type = lens_type
        instance.focal_length = focal_length
        instance.aperture = aperture
        instance.question_field_one = question_field_one
        instance.question_field_two = question_field_two
        instance.user = user
        instance.is_profile_camera_settings = not self.context.get('observation_settings')
        instance.save()

        return instance
