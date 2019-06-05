from django import forms
from django.utils.safestring import mark_safe

import datetime

from django.conf import settings

SUMMARY_FORM_SORT_CHOICES = (
    ('filing_id','Filing date'),
    ('period_individual_contribution_total','Individual contributions'),
    ('period_total_disbursements','Disbursements'),
    ('period_total_receipts','Receipts'),
    ('period_percent_unitemized','Percent unitemized'),
    ('period_disbursements_div_receipts','Burn rate'),
    ('cash_on_hand_close_of_period','Cash'),
    ('period_independent_expenditures','Independent Expenditures')
)

CYCLE_SUMMARY_FORM_SORT_CHOICES = (
    ('filing_id','Filing date'),
    ('cycle_individual_contribution_total','Individual contributions'),
    ('cycle_total_disbursements','Disbursements'),
    ('cycle_total_receipts','Receipts'),
    ('cycle_percent_unitemized','Percent unitemized'),
    ('cycle_disbursements_div_receipts','Burn rate'),
    ('cash_on_hand_close_of_period','Cash'),
    ('cycle_independent_expenditures','Independent Expenditures')
)

DIRECTION_CHOICES = (('DESC','descending'),('ASC','ascending'))

FORM_TYPE_CHOICES = (
    ('all','All'),
    ('F3P','Presidential (F3P)'),
    ('F3','House or Senate (F3)'),
    ('F3X','PAC or Party (F3X)'),
    ('F24','Independent Expenditure (F24)'),
    ('F5','Independent Expenditure (F5)')
    )

class ContributionForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    donor = forms.CharField(label='Donor name', max_length=500, required=False)
    employer = forms.CharField(label='Donor\'s employer or occupation', max_length=500, required=False)
    address = forms.CharField(label='Donor\'s street address, city and/or zipcode', max_length=500, required=False)
    include_memo = forms.BooleanField(label='Include memo entries', required=False)
    min_date = forms.CharField(label="Min receipt date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max receipt date (YYYYMMDD)", required=False)
    order_by = forms.ChoiceField(label="Sort field", initial="Contribution Amount", choices=(('contribution_amount', 'Contribution Amount'),('contribution_date', 'Contribution Date'), ('contributor_last_name','Contributor Last Name')), required=False)
    order_direction = forms.ChoiceField(label='Sort direction', choices=DIRECTION_CHOICES, initial='descending', required=False)

class ExpenditureForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    recipient = forms.CharField(label='recipient name', max_length=500, required=False)
    purpose = forms.CharField(label='expenditure purpose', max_length=500, required=False)
    address = forms.CharField(label='Recipient\'s street address, city and/or zipcode', max_length=500, required=False)    
    include_memo = forms.BooleanField(label='Include memo entries', required=False)
    min_date = forms.CharField(label="Min expend date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max expend date (YYYYMMDD)", required=False)
    order_by = forms.ChoiceField(label="Sort field", initial="Expenditure Amount", choices=(('expenditure_amount', 'Expenditure Amount'),('expenditure_date', 'Expenditure Date')), required=False)
    order_direction = forms.ChoiceField(label='Sort direction', choices=DIRECTION_CHOICES, initial='descending', required=False)

class IEForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    recipient = forms.CharField(label='recipient name', max_length=500, required=False)
    purpose = forms.CharField(label='expenditure purpose', max_length=500, required=False)
    candidate = forms.CharField(label='candidate', max_length=500, required=False)
    min_date = forms.CharField(label="Min ie date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max ie date (YYYYMMDD)", required=False)
    order_by = forms.ChoiceField(label="Sort field", initial="Expenditure Amount", choices=(('expenditure_amount', 'Expenditure Amount'),('expenditure_date', 'Expenditure Date')), required=False)
    order_direction = forms.ChoiceField(label='Sort direction', choices=DIRECTION_CHOICES, initial='descending', required=False)

class FilingForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    form_type = forms.ChoiceField(label='Filer type', choices=FORM_TYPE_CHOICES, initial='All', required=False)
    min_raised = forms.DecimalField(label='Minimum raised', required=False)
    exclude_amendments = forms.BooleanField(label='Exclude amendments', required=False)
    min_date = forms.CharField(label="Min filing date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max filing date (YYYYMMDD)", required=False)
    
class SummaryForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    form_type = forms.ChoiceField(label='Filer type', choices=FORM_TYPE_CHOICES, initial='All)', required=False)
    min_raised = forms.DecimalField(label='Minimum raised', required=False)
    min_date = forms.CharField(label="Min filing date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max filing date (YYYYMMDD)", required=False)
    cnn_committees = forms.BooleanField(label=mark_safe('Restrict to Saved Candidates (<a href="/admin/cycle_2020/candidate/">Add/Edit candidates list</a>)'), required=False) #This really belongs in the template, but WTH
    order_by = forms.ChoiceField(label="Sort field", initial="Filing date", choices=SUMMARY_FORM_SORT_CHOICES, required=False)
    order_direction = forms.ChoiceField(label='Sort direction', choices=DIRECTION_CHOICES, initial='descending', required=False)

class CycleSummaryForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    form_type = forms.ChoiceField(label='Filer type', choices=FORM_TYPE_CHOICES, initial='All', required=False)
    min_raised = forms.DecimalField(label='Minimum raised', required=False)
    min_date = forms.CharField(label="Min filing date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max filing date (YYYYMMDD)", required=False)
    cnn_committees = forms.BooleanField(label=mark_safe('Restrict to Saved Candidates (<a href="/admin/cycle_2020/candidate/">Add/Edit candidates list</a>)'), required=False) #This really belongs in the template, but WTH
    order_by = forms.ChoiceField(label="Sort field", initial="Filing date", choices=CYCLE_SUMMARY_FORM_SORT_CHOICES, required=False)
    order_direction = forms.ChoiceField(label='Sort direction', choices=DIRECTION_CHOICES, initial='descending', required=False)

class InauguralForm(forms.Form):
    name = forms.CharField(label='Contributor name', max_length=500, required=False)
