from django.contrib import admin
from donor.models import *

class DonorAdmin(admin.ModelAdmin):
    search_fields = ['cnn_name']
    ordering = ('cnn_name',)
    list_display = ('cnn_name','contribution_total_2020')

admin.site.register(Donor, DonorAdmin)