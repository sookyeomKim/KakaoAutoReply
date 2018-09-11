from storages.backends.s3boto3 import S3Boto3Storage


class UploadStorage(S3Boto3Storage):
    location = 'uploads'
    file_overwrite = True
