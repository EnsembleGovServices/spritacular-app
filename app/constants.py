# import pytz
#
# TIME_ZONES = pytz.all_timezones

# Validation Messages
NO_ACCOUNT = 'No active account found with the given credentials.'
ACCOUNT_ALREADY_EXISTS = 'user with this email already exists.'
FIELD_REQUIRED = '{} field may not be blank.'
SINGLE_IMAGE_VALID = 'Number of the images should not be more than 1.'
MULTIPLE_IMAGE_VALID = 'Number of the images should not be more than 3.'
PASS_CONFIRM_PASS_INVALID = 'password and confirm password does not match.'
NEW_PASS_CONFIRM_PASS_INVALID = 'New password and confirm password does not match.'
INVALID_OLD_PASS = 'Old password is incorrect.'
CAMERA_SETTINGS_ALREADY_EXISTS = 'Camera settings for this user already exists.'
CHANGE_PASS_SUCCESS = 'Password successfully changed.'
WELCOME = '<center><h1>Welcome to Spritacular</h1></center>'

# Response Messages
NOT_FOUND = {'detail': 'Not found.', 'status': 0}
CONTENT_NOT_FOUND = {'detail': 'Not found.', 'content': False, 'status': 0}
OBS_FORM_SUCCESS = {'success': 'Form submitted successfully', 'status': 1}
OBS_PUSH_BACK_SUCCESS = {'success': 'Observation successfully pushed back to user.', 'status': 1}
OBS_DRAFT_DELETE = {'success': 'Draft successfully deleted.', 'status': 1}
BLOG_FORM_SUCCESS = {'success': 'Blog created successfully', 'status': 1}
NOTIFICATION_READ_SUCCESS = "Notification read status changed successfully"

SOMETHING_WENT_WRONG = {'detail': 'Something went wrong.', 'status': 0}
INVALID_ACTION = {'detail': 'Invalid action for this observation.', 'status': 0}
