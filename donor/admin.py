from django.contrib import admin
from donor.models import *

class DonorAdmin(admin.ModelAdmin):
    search_fields = ['cnn_name']

admin.site.register(Donor, DonorAdmin)