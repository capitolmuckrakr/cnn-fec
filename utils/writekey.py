# coding: utf-8
from django.core.management.utils import get_random_secret_key
key = "export DJANGO_SECRET_KEY='"+get_random_secret_key()+"'"
with open('/home/ubuntu/scripts/cnn-fec-dotfiles/.env','a') as oldfile:
    oldfile.write(key)
    oldfile.write("\n")

