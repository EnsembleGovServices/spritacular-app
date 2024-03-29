import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import CustomUserManager

from django.dispatch import receiver
from django_rest_passwordreset.signals import reset_password_token_created
from django.core.mail import send_mail
from django.template.loader import render_to_string
from spritacular.settings import EMAIL_HOST_USER, FRONTEND_URL


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True


class User(AbstractUser):

    username = None
    uid = models.UUIDField(default=uuid.uuid4)
    email = models.CharField(max_length=1024, unique=True)
    location = models.CharField(max_length=256, null=True, blank=True)
    place_uid = models.CharField(max_length=256, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    profile_image = models.ImageField(null=True, blank=True, upload_to='profile_image')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True, null=True, blank=True)
    location_metadata = models.JSONField(null=True, blank=True)
    is_first_login = models.BooleanField(default=False)
    is_trained = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email}"


class CameraSetting(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera_type = models.CharField(max_length=30, null=True, blank=True)
    iso = models.CharField(max_length=10, null=True, blank=True)
    shutter_speed = models.CharField(max_length=10, null=True, blank=True)
    fps = models.CharField(max_length=10, null=True, blank=True, help_text="Frames per second")
    lens_type = models.CharField(max_length=20, null=True, blank=True)
    focal_length = models.CharField(max_length=10, null=True, blank=True)
    aperture = models.FloatField(null=True, blank=True)
    question_field_one = models.TextField(null=True, blank=True)
    question_field_two = models.TextField(null=True, blank=True)

    is_profile_camera_settings = models.BooleanField(default=True)

    class Meta:
        db_table = 'camera_setting'

    def __str__(self):
        return f"{self.user.email} - {self.camera_type}"


@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    email_plaintext_message = f"http://{FRONTEND_URL}/password_reset/?token={reset_password_token.key}"

    html_content = render_to_string('password_reset.html', context={'reset_link': email_plaintext_message})

    send_mail(
        # title:
        "Password reset link",
        # message:
        email_plaintext_message,
        # from:
        EMAIL_HOST_USER,
        # to:
        [reset_password_token.user.email],
        # email html content
        html_message=html_content
    )
