import os
import json
from mimetypes import MimeTypes
import logging
import redis
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

from .utils import (
    get_name_from_path,
    get_extension_from_path,
    get_default_for_json_dump
)

logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)

ONE_HOUR = 3600
ONE_DAY = 3600*24


class ObjectStorage():

    s3_config = Config(
        region_name='ru-central1',
        # signature_version = 'v4',  # default. If you need presigned_url > 7 days then v2
        retries={
            'max_attempts': 3,
            'mode': 'standard'
        }
    )

    S3_SERVICE_NAME = ''
    S3_ENDPOINT_URL = ''
    S3_BUCKET = ''
    REDIS_CONTAINER_NAME = ''

    def __init__(self,
                 s3_service_name='',
                 s3_endpoint_url='',
                 s3_bucket='',
                 redis_container_name=''):
        if s3_service_name:
            self.S3_SERVICE_NAME = s3_service_name
        if s3_endpoint_url:
            self.S3_ENDPOINT_URL = s3_endpoint_url
        if s3_bucket:
            self.S3_BUCKET = s3_bucket
        if redis_container_name:
            self.REDIS_CONTAINER_NAME = redis_container_name

        self.session = boto3.session.Session()
        self.s3 = self.session.client(
            service_name=self.S3_SERVICE_NAME,
            endpoint_url=self.S3_ENDPOINT_URL,
            config=self.s3_config
        )
        self.cache = redis.Redis(
            host=self.REDIS_CONTAINER_NAME,
            port=6379,
            decode_responses=True
        )

    def create_presigned_url(self, object_name, expiration=ONE_DAY*2, content_disposal='inline'):
        """Generate a presigned URL to share an S3 object

        :param bucket_name: string
        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """

        try:
            return self.s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.S3_BUCKET,
                    'Key': object_name,
                    'ResponseContentDisposition': content_disposal,
                },
                ExpiresIn=expiration
            )
        except ClientError as e:
            logging.error(e)
            return None

    def get_presigned_url(self, object_name, content_disposal='inline'):
        cache_key = f'{object_name}_{content_disposal}'
        presigned_url_from_cache = self.cache.get(cache_key)
        if presigned_url_from_cache:
            return presigned_url_from_cache
        new_presigned_url = self.create_presigned_url(
            object_name=object_name,
            content_disposal=content_disposal
        )
        self.cache.set(cache_key, new_presigned_url)
        self.cache.expire(cache_key, ONE_DAY)
        return new_presigned_url

    def get_metadata(self, object_name):
        cache_key = f'{object_name}_metadata'
        metadata_from_cache = self.cache.get(cache_key)
        if metadata_from_cache:
            return json.loads(metadata_from_cache)

        try:
            new_metadata = self.s3.head_object(
                Bucket=self.S3_BUCKET,
                Key=object_name,
            )
        except ClientError as e:
            logging.error(e)
            return {}

        new_metadata_as_str = json.dumps(
            new_metadata,
            default=get_default_for_json_dump
        )
        self.cache.set(cache_key, new_metadata_as_str)
        self.cache.expire(cache_key, ONE_DAY)
        return new_metadata

    def upload_file_from_location(self, file_location, object_name=None, metadata={}):

        if not object_name:
            object_name = file_location

        mime = MimeTypes()
        content_type = mime.guess_type(object_name)[0]
        if not content_type:
            content_type = 'application/octet-stream'

        r = self.s3.upload_file(
            file_location,
            self.S3_BUCKET,
            object_name,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': {
                    **{
                        'filesize': str(os.path.getsize(file_location)),
                        'extension': get_extension_from_path(object_name),
                        'name': get_name_from_path(object_name)
                    },
                    **metadata
                },
            }
        )

    def upload_file(self, file, object_name=None, storage_class='STANDARD', content_type=None, metadata={}):
        # If S3 object_name was not specified, use file_name
        if not object_name:
            object_name = os.path.basename(file.name)

        if not content_type:
            try:
                content_type = file.content_type
            except AttributeError:
                content_type = 'application/octet-stream'

        try:
            r = self.s3.put_object(
                Bucket=self.S3_BUCKET,
                Key=object_name,
                Body=file,
                ContentType=content_type,
                StorageClass=storage_class,
                Metadata={
                    **{
                        'filesize': str(len(file)),
                        'extension': get_extension_from_path(object_name),
                        'name': get_name_from_path(object_name)
                    },
                    **metadata
                },
            )
        except ClientError as e:
            logging.error(e)

    def delete_file(self, object_name):
        self.cache.delete(object_name)
        try:
            self.s3.delete_object(Bucket=self.S3_BUCKET, Key=object_name)
        except Exception as e:
            logging.error(e)

    def replace_file(self, file, prev_object_name, next_object_name):
        # mb use versining instead
        self.delete_file(prev_object_name)
        self.upload_file(file, next_object_name)

    def list_bucket(self):
        flist = []
        try:
            for key in self.s3.list_objects(Bucket=self.S3_BUCKET)['Contents']:
                flist.append(key['Key'])
        except KeyError:
            print('no Contents')
        return flist

    def get_object(self, name):
        response = self.s3.get_object(
            Bucket=self.S3_BUCKET,
            Key=name
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return response['Body'].read()
        else:
            return None
