from django.conf import settings
from storages.backends.s3boto import S3BotoStorage
import boto3, os
from boto.s3.connection import S3Connection
sts = boto3.client('sts')
response = sts.assume_role(
    RoleArn='arn:aws:iam::704368634799:role/fecproject-alex',
    RoleSessionName='cnndigitalfecprojectalex'
)
credentials = response['Credentials']
os.environ['AWS_SESSION_TOKEN']=credentials['SessionToken']
os.environ['AWS_ACCESS_KEY_ID']=credentials['AccessKeyId']
os.environ['AWS_SECRET_ACCESS_KEY']=credentials['SecretAccessKey']
c = S3Connection(
    os.getenv('AWS_ACCESS_KEY_ID'),
    os.getenv('AWS_SECRET_ACCESS_KEY'),
    security_token=os.getenv('AWS_SESSION_TOKEN')
)

class StaticStorage(S3BotoStorage):
    connection = c
    location = settings.STATICFILES_LOCATION

class MediaStorage(S3BotoStorage):
    connection = c
    location = settings.MEDIAFILES_LOCATION