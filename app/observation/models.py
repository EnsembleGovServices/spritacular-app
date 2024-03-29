import datetime

import pytz
from django.db import models
from django.dispatch import receiver

from users.models import User, CameraSetting, BaseModel


class Observation(BaseModel):
    SINGLE_IMAGE = 1
    # MULTIPLE_IMAGE = 2
    SEQUENCE_IMAGE = 3

    IMAGE_TYPE = [
        (SINGLE_IMAGE, 'Single image'),
        # (MULTIPLE_IMAGE, 'Multiple images from same or different observation.'),
        (SEQUENCE_IMAGE, 'Images sequence from video recorded.'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    camera = models.ForeignKey(CameraSetting, on_delete=models.SET_NULL, null=True, blank=True)
    image_type = models.PositiveSmallIntegerField(choices=IMAGE_TYPE, default=SINGLE_IMAGE)
    is_verified = models.BooleanField(default=False)
    is_reject = models.BooleanField(default=False)
    is_to_be_verify = models.BooleanField(default=False)
    is_submit = models.BooleanField(default=False)
    reject_message = models.TextField(null=True, blank=True)
    elevation_angle = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    story = models.TextField(default='', blank=True)
    active_tab = models.JSONField(default=dict)

    verified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='verified_by')
    media_file_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"Observation by {self.user.email}"


class ObservationImageMapping(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='observation_image', null=True, blank=True)
    compressed_image = models.ImageField(upload_to='compressed_observation_image', null=True, blank=True)
    image_name = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=256, null=True, blank=True)
    place_uid = models.CharField(max_length=256, null=True, blank=True)
    country_code = models.CharField(max_length=10, null=True, blank=True)
    latitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True)
    obs_date = models.DateField(null=True, blank=True)
    obs_time = models.TimeField(null=True, blank=True)
    obs_date_time_as_per_utc = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)
    azimuth = models.CharField(max_length=10, null=True, blank=True)
    is_precise_azimuth = models.BooleanField(default=False)
    time_accuracy = models.CharField(max_length=20, null=True, blank=True)

    def set_utc(self):
        try:
            time_zone = pytz.timezone(self.timezone)
            observe_time = str(self.obs_time).split(':')
            obs_start_time = datetime.datetime.combine(self.obs_date, datetime.time(int(observe_time[0]),
                                                                                    int(observe_time[1])))
            start_time = time_zone.localize(obs_start_time)
            dt_start = start_time.astimezone(pytz.utc)
            self.obs_date_time_as_per_utc = dt_start
            self.save(update_fields=['obs_date_time_as_per_utc'])
        except Exception as e:
            print(e)
        return True


class ObservationReasonForReject(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    additional_comment = models.TextField(default='', blank=True)
    inappropriate_image = models.BooleanField(default=False)
    other = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.id} | Observation id - {self.observation.id}"

    class Meta:
        db_table = 'observation_reason_for_reject'


class Category(BaseModel):
    title = models.CharField(max_length=20, unique=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title}"


class ObservationCategoryMapping(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.observation.id}, {self.category.title}"

    class Meta:
        db_table = 'observation_category_mapping'


class ObservationLike(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'observation_like'


class ObservationWatchCount(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'observation_watch_count'


class VerifyObservation(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vote = models.BooleanField(default=False)

    class Meta:
        db_table = 'verify_observation'


class ObservationComment(BaseModel):
    observation = models.ForeignKey(Observation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'observation_comment'


@receiver(models.signals.post_delete, sender=ObservationImageMapping)
def remove_file_from_s3(sender, instance, using, **kwargs):
    instance.image.delete(save=False)
    print("Observation image s3 file deleted")
    instance.compressed_image.delete(save=False)
    print("Observation compressed_image s3 file deleted")
