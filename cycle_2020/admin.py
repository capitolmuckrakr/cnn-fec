from django.contrib import admin
from cycle_2020.models import *
import datetime

class ScheduleEAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def formatted_amount(self, obj):
        try:
            return '${:,.2f}'.format(obj.expenditure_amount)
        except:
            return '${:,.2f}'.format(0)

    view_on_site = False
    ordering = ['-expenditure_amount']
    list_display = ['committee_name',
                    'support',
                    'candidate_name',
                    'cnn_district',
                    'formatted_amount',
                    'expenditure_date_formatted',
                    ]
    list_filter =   [
                    'support_oppose_code',
                    'candidate_office',
                    'candidate_state',
                    'candidate_district',
                    ]
    readonly_fields = ['committee_name',
                    'expenditure_amount',
                    'candidate_first_name',
                    'candidate_last_name',
                    'candidate_office',
                    'candidate_state',
                    'candidate_district',
                    'filing_id',
                    ]
    fields = readonly_fields + ['cnn_district', 'active']

class CommitteeAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    ordering = ['committee_name']
    readonly_fields = ['fec_id',
                    'street_1',
                    'street_2',
                    'city',
                    'state',
                    'zipcode',
                    'treasurer_last_name',
                    'treasurer_first_name',
                    'treasurer_middle_name',
                    'treasurer_prefix',
                    'treasurer_suffix',
                    'committee_type',
                    'committee_designation',
                    ]
    search_fields = ['committee_name',
                    'fec_id',
                    ]
    fields = readonly_fields + ['committee_name']
    
class ScheduleAAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(form_type__in=['SA17A','SA17','SA11AI'], contribution_amount__gte=100000, active=True).exclude(contributor_organization_name__icontains='unitemized').exclude(contributor_last_name__icontains='unitemized').exclude(contributor_first_name__icontains='unitemized')

    def formatted_amount(self, obj):
        try:
            return '${:,.2f}'.format(obj.contribution_amount)
        except:
            return '${:,.2f}'.format(0)
    
    def contribution_date_sorting(self, obj):
        date_str = obj.contribution_date
        y, m, d = int(date_str[:4]),int(date_str[4:6]),int(date_str[6:])
        return datetime.date(y,m,d)

    def employer_occupation(self, obj):
        if obj.contributor_occupation and obj.contributor_employer:
            return "{} | {}".format(obj.contributor_employer,obj.contributor_occupation)
        if obj.contributor_occupation:
            return obj.contributor_occupation
        if obj.contributor_employer:
            return obj.contributor_employer
        return ""

    ordering = ['-contribution_amount']
    list_display = ['contributor_name',
                    'donor',
                    'employer_occupation',
                    'committee_name',
                    'contribution_date_formatted',
                    'formatted_amount',
                    ]
    list_editable = ['donor']
    readonly_fields = ['committee_name',
                    'contributor_name',
                    'contributor_suffix',
                    'contributor_employer',
                    'contributor_occupation',
                    'address',
                    'form_type',
                    'formatted_amount',
                    'contribution_date_formatted'
                    ]
    autocomplete_fields = ['donor']
    search_fields = ['contributor_first_name',
                    'contributor_last_name',
                    'contributor_organization_name',
                    'form_type',
                    'filer_committee_id_number',
                    'filing_id']
    fields = readonly_fields+autocomplete_fields

class CandidateAdmin(admin.ModelAdmin):
    search_fields = ['name']
    ordering = ('office','name')
    list_filter = ('active','office','party','state','incumbent')
    list_display = ('name','office','state','party','incumbent','active')

admin.site.register(ScheduleA, ScheduleAAdmin)
admin.site.register(ScheduleE, ScheduleEAdmin)
admin.site.register(Candidate, CandidateAdmin)
admin.site.register(Committee, CommitteeAdmin)
