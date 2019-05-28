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

def index(request):
    return render(request, '2020/index.html', { 'contact':settings.CONTACT})

def get_summary_results(request):
    comm = request.GET.get('committee')
    form_type = request.GET.get('form_type')
    min_raised = request.GET.get('min_raised')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    
    results = Filing.objects.filter(active=True)
    if comm:
        results = results.annotate(search=SearchVector('committee_name','filer_id'),).filter(search=comm)
    if form_type:
        results = results.filter(form=form_type)
    if min_raised:
        results = results.filter(period_total_receipts__gte=min_raised)
    if min_date:
        results = results.filter(date_signed__gte=min_date)
    if max_date:
        results = results.filter(date_signed__lte=max_date)

    order_by = request.GET.get('order_by', 'filing_id')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_by == 'period_disbursements_div_receipts':
        try:
            results = results.annotate(
                ordering=Case(
                    When(period_total_receipts=0, then=0),
                    default=F('period_total_disbursements') / F('period_total_receipts'))).order_by('ordering')
            if order_direction == "DESC":
                results = results.reverse()
                return results
        except:
            return results
    elif order_by == 'period_percent_unitemized':
        try:
            results = results.annotate(
                ordering=Case(
                    When(period_total_contributions=0, then=0),
                    default=F('period_individuals_unitemized') / F('period_total_contributions'))).order_by('ordering')
            if order_direction == "DESC":
                results = results.reverse()
                return results
        except:
            return results
    else:
        results = results.order_by(order_by)
    if order_direction == "DESC":
        results = results.order_by('-{}'.format(order_by))
    else:
        results = results.order_by(order_by)
    return results

def summary(request):
    form = SummaryForm(request.GET)
    if not request.GET:
        return render(request, '2020/summary_001.html', {'form': form, 'opts': ScheduleA._meta, 'contact':settings.CONTACT})
    results = get_summary_results(request)
    
    #csv_url = reverse('2020:contributions_csv') + "?"+ request.GET.urlencode()
    
    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    return render(request, '2020/summary_001.html', {'form': form, 'results':results, 'opts': ScheduleA._meta, 'contact':settings.CONTACT})

def get_cycle_summary_results(request):
    comm = request.GET.get('committee')
    form_type = request.GET.get('form_type')
    min_raised = request.GET.get('min_raised')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    
    results = Filing.objects.filter(active=True)
    if comm:
        results = results.annotate(search=SearchVector('committee_name','filer_id'),).filter(search=comm)
    if form_type:
        results = results.filter(form=form_type)
    if min_raised:
        results = results.filter(cycle_total_receipts__gte=min_raised)
    if min_date:
        results = results.filter(date_signed__gte=min_date)
    if max_date:
        results = results.filter(date_signed__lte=max_date)

    order_by = request.GET.get('order_by', 'filing_id')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_by == 'cycle_disbursements_div_receipts':
        try:
            results = results.annotate(
                ordering=Case(
                    When(cycle_total_receipts=0, then=0),
                    default=F('cycle_total_disbursements') / F('cycle_total_receipts'))).order_by('ordering')
            if order_direction == "DESC":
                results = results.reverse()
                return results
        except:
            return results
    elif order_by == 'cycle_percent_unitemized':
        try:
            results = results.annotate(
                ordering=Case(
                    When(cycle_total_contributions=0, then=0),
                    default=F('cycle_individuals_unitemized') / F('cycle_total_contributions'))).order_by('ordering')
            if order_direction == "DESC":
                results = results.reverse()
                return results
        except:
            return results
    else:
        results = results.order_by(order_by)
    if order_direction == "DESC":
        results = results.order_by('-{}'.format(order_by))
    else:
        results = results.order_by(order_by)
    return results

def cycle_summary(request):
    form = CycleSummaryForm(request.GET)
    if not request.GET:
        return render(request, '2020/cycle_summary.html', {'form': form, 'opts': ScheduleA._meta, 'contact':settings.CONTACT})
    results = get_cycle_summary_results(request)
    
    #csv_url = reverse('2020:contributions_csv') + "?"+ request.GET.urlencode()
    
    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    return render(request, '2020/cycle_summary.html', {'form': form, 'results':results, 'opts': ScheduleA._meta, 'contact':settings.CONTACT})

def get_contribution_results(request):
    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    donor = request.GET.get('donor')
    employer = request.GET.get('employer')
    address = request.GET.get('address')
    include_memo = request.GET.get('include_memo')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    form_type = request.GET.get('form_type')

    results = ScheduleA.objects.filter(active=True)
    if not include_memo:
        results = results.exclude(status='MEMO')
    if filing_id:
        results = results.filter(filing_id=filing_id)
    if employer:
        query = SearchQuery(employer)
        results = results.filter(occupation_search=query)
    if donor:
        query = SearchQuery(donor)
        results = results.filter(name_search=query)
    if address:
        query = SearchQuery(address)
        results = results.filter(address_search=query)
    if min_date:
        results = results.filter(contribution_date__gte=min_date)
    if max_date:
        results = results.filter(contribution_date__lte=max_date)
    if form_type:
        results = results.filter(form_type=form_type)

    if comm:
        matching_committees = Committee.find_committee_by_name(comm)
        comm_ids = [c.fec_id for c in matching_committees]
        results = results.filter(filer_committee_id_number__in=comm_ids)

    order_by = request.GET.get('order_by', 'contribution_amount')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_direction == "DESC":
        results = results.order_by('-{}'.format(order_by))
    else:
        results = results.order_by(order_by)
    return results

def contributions(request):
    form = ContributionForm(request.GET)
    if not request.GET:
        return render(request, '2020/contributions.html', {'form': form,  'contact':settings.CONTACT})

    results = get_contribution_results(request)

    results_sum = None if request.GET.get('include_memo') else results.aggregate(Sum('contribution_amount'))

    csv_url = reverse('2020:contributions_csv') + "?"+ request.GET.urlencode()

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    
    return render(request, '2020/contributions.html', {'form': form, 'results':results, 'results_sum':results_sum, 'csv_url':csv_url, 'contact':settings.CONTACT})

def contributions_csv(request):
    results = get_contribution_results(request)
    filename = "ScheduleA_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    def rows():
        yield ScheduleA.export_fields()
        for result in results:
            yield result.csv_row()

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

def presidential_csv(request):
    deadline = request.GET.get('deadline')

    results = Candidate.objects.filter(office='P').order_by('party', 'name')
    filename = "Candidates_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    candidate_fields = ['name', 'office', 'party', 'incumbent']
    filing_fields = ['filing_id','form','filer_id',
            'committee_name', 'cash_on_hand_close_of_period', 'is_amendment',
            'period_total_receipts','cycle_total_receipts',
            'period_total_disbursements', 'cycle_total_disbursements',
            'period_individuals_unitemized', 'cycle_individuals_unitemized',
            'period_individuals_itemized', 'cycle_individuals_itemized',
            'period_transfers_from_authorized','cycle_transfers_from_authorized',
            'period_individual_contribution_total', 'cycle_individual_contribution_total',
            'coverage_from_date', 'coverage_through_date']

    def rows_with_totals():
        yield candidate_fields+filing_fields+['cycle_candidate_donations_plus_loans','period_candidate_donations_plus_loans']
        for result in results:
            if deadline:
                filing = result.filing_by_deadline(deadline)
            else:
                filing = result.most_recent_filing()

            row = []
            for f in candidate_fields:
                value = getattr(result, f)
                if value is None:
                    row.append("")
                else:
                    row.append(value)
            for f in filing_fields:
                if not filing:
                    if f == 'filer_id':
                        #if there is no filing, use the candidate's committee id
                        value = getattr(result, "fec_committee_id")
                        if value is not None:
                            row.append(value)
                            continue
                    row.append("")
                    continue
                value = getattr(filing, f)
                if value is None:
                    row.append("")
                else:
                    row.append(value)
            if filing:
                cycle_candidate_donations_plus_loans = filing.cycle_candidate_donations_plus_loans #this has to be done separately bc it's a property.
                period_candidate_donations_plus_loans = filing.period_candidate_donations_plus_loans
            if not filing or cycle_candidate_donations_plus_loans is None:
                row.append("")
            else:
                row.append(cycle_candidate_donations_plus_loans)
            if not filing or period_candidate_donations_plus_loans is None:
                row.append("")
            else:
                row.append(period_candidate_donations_plus_loans)
            yield row


    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows_with_totals()),
                                     content_type="text/csv")

    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response
