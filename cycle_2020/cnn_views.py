import datetime
import re
import csv
import time

from django.shortcuts import render
from django.db.models import Q, Sum, F, Case
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.http import StreamingHttpResponse
from django.urls import reverse

from cycle_2020.models import *
from cycle_2020.forms import *
from donor.models import Donor

class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def get_summary_results(request):
    comm = request.GET.get('committee')
    form_type = request.GET.get('form_type')
    min_raised = request.GET.get('min_raised')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    cnn_committees = request.GET.get('cnn_committees')
    
    results = Filing.objects.filter(active=True)
    if comm:
        results = results.annotate(search=SearchVector('committee_name','filer_id'),).filter(search=comm)
    if form_type:
        if not form_type == 'all':
            results = results.filter(form=form_type)
    if min_raised:
        results = results.filter(period_total_receipts__gte=min_raised)
    if min_date:
        results = results.filter(date_signed__gte=min_date)
    if max_date:
        results = results.filter(date_signed__lte=max_date)
    if cnn_committees:
        cand_filer_ids= Candidate.objects.all().values('fec_committee_id')
        results = results.filter(filer_id__in=cand_filer_ids)

    order_by = request.GET.get('order_by', 'filing_id')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_by == 'period_disbursements_div_receipts':
        results = results.filter(period_total_receipts__gt=0)
        try:
            if order_direction == "DESC":
                results = sorted(results, key = lambda x: x.period_disbursements_div_receipts, reverse=True)
            else:
                results = sorted(results, key = lambda x: x.period_disbursements_div_receipts)
        except:
            return results
    elif order_by == 'period_percent_unitemized':
        results = results.filter(period_total_contributions__gt=0)
        try:
            if order_direction == "DESC":
                results = sorted(results, key = lambda x: x.period_percent_unitemized, reverse=True)
            else:
                results = sorted(results, key = lambda x: x.period_percent_unitemized)
        except:
            return results
    else:
        if order_direction == "DESC":
            results = results.order_by('-{}'.format(order_by))
        else:
            results = results.order_by(order_by)
    return results

def summary(request):
    form = SummaryForm(request.GET)
    results = get_summary_results(request)
    
    csv_url = reverse('2020:summary_csv') + "?"+ request.GET.urlencode()
    cycle_summary_url = reverse('2020:cycle_summary') + "?"+ request.GET.urlencode().replace('period_','cycle_')
    
    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    return render(request, '2020/summary_001.html', {'form': form, 'results':results, 'opts': ScheduleA._meta,'csv_url':csv_url, 'cycle_summary_url':cycle_summary_url, 'contact':settings.CONTACT})

def summary_csv(request):
    results = get_summary_results(request)
    filename = "Summary_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    def rows():
        yield Filing.export_fields()
        for result in results:
            yield result.csv_row()

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

def get_cycle_summary_results(request):
    comm = request.GET.get('committee')
    form_type = request.GET.get('form_type')
    min_raised = request.GET.get('min_raised')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    cnn_committees = request.GET.get('cnn_committees')
    
    results = Filing.objects.filter(active=True)
    if comm:
        results = results.annotate(search=SearchVector('committee_name','filer_id'),).filter(search=comm)
    if form_type:
        if not form_type == 'all':
            results = results.filter(form=form_type)
    if min_raised:
        results = results.filter(cycle_total_receipts__gte=min_raised)
    if min_date:
        results = results.filter(date_signed__gte=min_date)
    if max_date:
        results = results.filter(date_signed__lte=max_date)
    if cnn_committees:
        cand_filer_ids= Candidate.objects.all().values('fec_committee_id')
        results = results.filter(filer_id__in=cand_filer_ids)

    order_by = request.GET.get('order_by', 'filing_id')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_by == 'cycle_disbursements_div_receipts':
        results = results.filter(cycle_total_receipts__gt=0)
        try:
            if order_direction == "DESC":
                results = sorted(results, key = lambda x: x.cycle_disbursements_div_receipts, reverse=True)
            else:
                results = sorted(results, key = lambda x: x.cycle_disbursements_div_receipts)
        except:
            return results
    elif order_by == 'cycle_percent_unitemized':
        results = results.filter(cycle_total_contributions__gt=0)
        try:
            if order_direction == "DESC":
                results = sorted(results, key = lambda x: x.cycle_percent_unitemized, reverse=True)
            else:
                results = sorted(results, key = lambda x: x.cycle_percent_unitemized)
        except:
            return results
    else:
        if order_direction == "DESC":
            results = results.order_by('-{}'.format(order_by))
        else:
            results = results.order_by(order_by)
    return results

def cycle_summary(request):
    form = CycleSummaryForm(request.GET)
    results = get_cycle_summary_results(request)
    
    csv_url = reverse('2020:cycle_summary_csv') + "?"+ request.GET.urlencode()
    period_summary_url = reverse('2020:summary') + "?"+ request.GET.urlencode().replace('cycle_','period_')
    
    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    return render(request, '2020/cycle_summary.html', {'form': form, 'results':results, 'opts': ScheduleA._meta, 'csv_url':csv_url, 'period_summary_url':period_summary_url, 'contact':settings.CONTACT})

def cycle_summary_csv(request):
    results = get_cycle_summary_results(request)
    filename = "Summary_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    def rows():
        yield Filing.export_fields()
        for result in results:
            yield result.csv_row()

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

