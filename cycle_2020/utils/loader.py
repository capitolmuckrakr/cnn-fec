import pytz
import datetime
import os
import requests
import csv
import time
import traceback
import sys
import urllib3
import lxml
import itertools
import logging as canon_logging
from decimal import Decimal
from cycle_2020.utils import logging
from cycle_2020.utils import unreadable_files

from bs4 import BeautifulSoup

import process_filing #this is from fec2json

from cycle_2020.models import *
from django.conf import settings
from django.template.defaultfilters import pluralize

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logger = canon_logging.getLogger('cnn-fec.'+__name__)
logger.setLevel(LOGLEVEL)

ACCEPTABLE_FORMS = ['F3','F3X','F3P','F24', 'F5']
BAD_COMMITTEES = ['C00401224','C00630012'] #actblue; it starts today
API_KEY = os.environ.get('FEC_API_KEY')
try:
    assert API_KEY
except AssertionError as err:
    logger.warning("Cannot find a FEC api key, please add as environment variable FEC_API_KEY",extra={'SYSLOG_IDENTIFIER':os.environ.get('SYSLOG_IDENTIFIER','')})
    raise err

from cycle_2020.cycle_settings import CYCLE
def get_filing_list(start_date, end_date, max_fails=10, waittime=10, myextra=None):
    #gets list of available filings from the FEC.
    #TODO: institute an API key pool or fallback?
    url = "https://api.open.fec.gov/v1/efile/filings/?per_page=100&sort=-receipt_date"
    url += "&api_key={}".format(API_KEY)
    url += "&min_receipt_date={}".format(start_date)
    url += "&max_receipt_date={}".format(end_date)

    filings = []
    page = 1
    fails = 0

    while True:
        #get new filing ids from FEC API
        resp = requests.get(url+"&page={}".format(page))
        page += 1
        if myextra:
            myextra=myextra.copy()
        try:
            files = resp.json()
        except:
            #failed to convert respons to JSON
            fails += 1
            if fails >= max_fails:
                logging.log(title="FEC download failed",
                    text='Failed to download valid JSON from FEC site {} times'.format(max_fails),
                    tags=["cnn-fec", "result:fail"])
                if myextra:
                    myextra['TAGS']='cnn-fec, result:fail'
                logger.warning('Failed to download valid JSON from FEC site {} times'.format(max_fails),
                               extra=myextra)
                return None
            time.sleep(waittime)
        try:
            results = files['results']
        except KeyError:
            fails += 1
            if fails >= max_fails:
                logging.log(title="FEC download failed",
                    text='Failed to download valid JSON from FEC site {} times'.format(max_fails),
                    tags=["cnn-fec", "result:fail"])
                if myextra:
                    myextra['TAGS']='cnn-fec, result:fail'
                logger.warning('Failed to download valid JSON from FEC site {} times'.format(max_fails),
                               extra=myextra)
                return None
            time.sleep(waittime)
            continue

        if len(results) == 0:
            break
        for f in results:
            if evaluate_filing(f):
                filings.append(f['file_number'])

    return filings

def filing_list_from_rss():
    #backup scraper if api craps out. Will get whatever is
    #currently in the rss feed, so no dates. We should probably
    #run this occasionally on filing nights.
    http = urllib3.PoolManager()
    response = http.request('GET', 'http://efilingapps.fec.gov/rss/generate?preDefinedFilingType=ALL')
    soup = BeautifulSoup(response.data, "lxml")
    items = soup.findAll('item')
    filings = []
    for item in items:
        #make a dictionary that will match what we would have gotten from the api
        filing = {}
        filing_info = item.find('description').text
        filing_info_list = filing_info.split("CommitteeId")[1].split('|')
        filing['committee_id'] = filing_info_list[0].replace(":","").strip()
        filing['file_number'] = filing_info_list[1].replace("FilingId:","").strip()
        filing['form_type'] = filing_info_list[2].replace("FormType:","").strip()
        coverage_through = filing_info_list[4].replace('CoverageThrough:','').strip()
        filing['coverage_end_date'] = coverage_through[6:]+coverage_through[0:2]+coverage_through[3:5]

        if evaluate_filing(filing):
            filings.append(filing['file_number'])
    return filings

def filing_list_from_classic():
    #backup backup scraper for the classic website which seem to be ahead sometimes
    http = urllib3.PoolManager()
    dates = []
    now = datetime.datetime.now()
    dates.append(now.strftime('%m/%d/%Y'))
    yesterday = now-datetime.timedelta(days=1)
    dates.append(yesterday.strftime('%m/%d/%Y'))
    tomorrow = now+datetime.timedelta(days=1)
    dates.append(tomorrow.strftime('%m/%d/%Y'))
    filings = []
    for d in dates:
        data = "comid=C&date={}&name=&state=&frmtype=&rpttype=&submit=Send+Query".format(d)
        response = http.request('POST', 'http://docquery.fec.gov/cgi-bin/forms/', body=data)
        soup = BeautifulSoup(response.data, "lxml")
        trs = soup.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            if len(tds) == 9:
                filing = {}
                filing['form_type'] = tds[0].text
                filing['file_number'] = tds[1].text.replace('FEC-','')
                coverage_through = tds[4].text.strip()
                filing['coverage_end_date'] = coverage_through[6:]+coverage_through[0:2]+coverage_through[3:5]
                link = tds[7].a['href']
                filing['committee_id'] = link.split('/')[-3]
                if evaluate_filing(filing):
                    filings.append(filing['file_number'])

    return filings

def evaluate_filing(filing):
    #determines whether filings in the API should be downloaded
    coverage_end = filing['coverage_end_date']
    if (check_existing_filings(filing)
        and remove_bad_committees(filing)
        and check_acceptable_forms(filing)
        and check_coverage_dates(filing, coverage_end_date)):
            create_or_update_filing_status(filing['file_number'], 'REFUSED')
            return False

    return True

def check_existing_filings(filing):
    #check whether we've already marked this filing as bad
    filing_id = filing['file_number']
    existing_filings = FilingStatus.objects.filter(filing_id=filing_id)
    if len(existing_filings) > 0:
        #remove filings that were successful
        if existing_filings[0].status in ['SUCCESS','REFUSED']:
            #print('already seen')
            return False
        else:
            #include filings that failed or are missing a status marker
            return True

def remove_bad_committees(filing):
    #remove bad committees:
    if filing['committee_id'] in BAD_COMMITTEES:
        #print('bad committee')
        return False
    return True

def check_acceptable_forms(filing):
    #remove filing types we're not loading
    if filing['form_type'].replace('A','').replace('N','') not in ACCEPTABLE_FORMS:
        #print('bad form type')
        return False
    return True

def check_coverage_dates(filing, coverage_end):
    #remove filings whose coverage period ended outside the current cycle
    if coverage_end:
        coverage_end_year = coverage_end[0:4]
        #print(coverage_end_year)
        if filing['form_type'] in ['F3PN', 'F3PA'] and CYCLE % 4 == 0:
            #if it's a presidential filing, we want it if it's in the 4-year period.
            acceptable_years = [CYCLE, CYCLE-1, CYCLE-2, CYCLE-3]
        else:
            acceptable_years = [CYCLE, CYCLE-1]
        #print(acceptable_years)
        if int(coverage_end_year) not in acceptable_years:
            #print('bad year')
            return False
    return True


def download_filings(filings, filing_dir="filings/", myextra=None):
    #takes a list of filing ids, downloads the files
    try:
        if filings:
            http = urllib3.PoolManager()
            existing_filings = os.listdir(filing_dir)
            for filing in filings:
                #download filings
                filename = '{}{}.csv'.format(filing_dir, filing)
                if myextra:
                    myextra=myextra.copy()
                    myextra['FILING']=str(filing)
                if filename not in existing_filings:
                    file_url = 'http://docquery.fec.gov/csv/{}/{}.csv'.format(str(filing)[-3:],filing)
                    if os.path.isfile(filename):
                        logger.debug('we already downloaded {}'.format(filing),extra=myextra)
                    #    sys.stdout.write("we already have filing {} downloaded\n".format(filing))
                    else:
                        response = http.request('GET', file_url)
                        with open(filename,'wb') as f:
                            f.write(response.data)
                        logger.info('downloaded {}'.format(filing),extra=myextra)
                        #os.system('curl -o {} {}'.format(filename, file_url))
        else:
            logger.warning('Missing required list of filings to download or list is empty',extra=myextra)
    except Exception as e:
        logger.error("Failed to download from FEC site",extra=myextra)

def load_itemizations(sked_model, skeds, debug=False):
    #if debug is true, we'll load one at a time, otherwise bulk_create
    sked_count = 0
    if debug:
        for line in skeds:
            if 'memo_code' in line and line['memo_code'] == 'X':
                line['status'] = 'MEMO'
            sked_model.objects.create(**line)
            sked_count += 1
    else:
        chunk_size = 5000
        chunk = []
        for line in skeds:
            sked_count += 1
            if line['form_type'].startswith('SB28') or line['form_type'].startswith('SB20'):
                #these are refunds and should be processed as contribs
                #we're going to create them individually to prevent trouble
                refund = convert_refund_to_skeda(line)
                ScheduleA.objects.create(**refund)
                continue

            if 'memo_code' in line and line['memo_code'] == 'X':
                line['status'] = 'MEMO'

            if line['form_type'].startswith('SE') or line['form_type'].startswith('F57'):
                nulls = ["0","00",""," "]
                #fix the district
                office = line['candidate_office']
                district = line['candidate_district']
                state = line['candidate_state']
                office_exists = office is not None and office not in nulls
                state_exists = state is not None and state not in nulls
                district_exists = district is not None and district not in nulls
                if office == "P":
                    line['cnn_district'] = "PRESIDENT"
                elif office_exists and state_exists and district_exists:
                    line['cnn_district'] = "{}-{}".format(state,district)
                elif office == 'S':
                    if state_exists:
                        line['cnn_district'] = "{}-SEN".format(state)
                    else:
                        line['cnn_district'] = "UNKNOWN"
                elif state_exists:
                    if state in ['AK','DE','MT','ND','SD','VT','WY']:
                        line['cnn_district'] = "{}-AT-LARGE".format(state)
                    else:
                        line['cnn_district'] = "{}-HOUSE-UNKNOWN".format(state)
                else:
                    line['cnn_district'] = "UNKNOWN"

            chunk.append(sked_model(**line))
            if len(chunk) >= chunk_size:
                sked_model.objects.bulk_create(chunk)
                chunk = []
        sked_model.objects.bulk_create(chunk)
    return sked_count

def convert_refund_to_skeda(line):
    common_fields = ['form_type',
                    'filer_committee_id_number',
                    'filing_id',
                    'transaction_id',
                    'back_reference_tran_id_number',
                    'back_reference_sched_name',
                    'entity_type',
                    'election_code',
                    'election_other_description',
                    'memo_code',
                    'memo_text_description'
                    ]
    skeda_dict = {}
    for field in common_fields:
        skeda_dict[field] = line[field]
    skeda_dict['contributor_organization_name'] = line['payee_organization_name']
    skeda_dict['contributor_last_name'] = line['payee_last_name']
    skeda_dict['contributor_first_name'] = line['payee_first_name']
    skeda_dict['contributor_middle_name'] = line['payee_middle_name']
    skeda_dict['contributor_prefix'] = line['payee_prefix']
    skeda_dict['contributor_suffix'] = line['payee_suffix']
    skeda_dict['contributor_street_1'] = line['payee_street_1']
    skeda_dict['contributor_street_2'] = line['payee_street_2']
    skeda_dict['contributor_city'] = line['payee_city']
    skeda_dict['contributor_state'] = line['payee_state']
    skeda_dict['contributor_zip'] = line['payee_zip']
    skeda_dict['contribution_date'] = line['expenditure_date']
    skeda_dict['contribution_amount'] = -1*Decimal(line['expenditure_amount'])
    
    return skeda_dict

def reassign_standardized_donors(filing_id, amended_id):
    #find all skeda's with donors from the amended filing
    #that we're about to deactivate
    matched_transactions = ScheduleA.objects.filter(filing_id=amended_id).exclude(donor=None)
    i = 0
    for transaction in matched_transactions:
        transaction_id = transaction.transaction_id
        contributor_last_name = transaction.contributor_last_name
        new_trans = ScheduleA.objects.filter(transaction_id=transaction_id, filing_id=filing_id)
        if len(new_trans) == 0:
            logging.log(title="donor reassignment issue",
                    text="filing {} was amended by filing {} and no transaction could be found for donor reassigment for transaction id {}".format(amended_id, filing_id, transaction_id),
                    tags=["cnn-fec", "result:warning"])
            continue
        if len(new_trans) > 1:
            logging.log(title="donor reassignment issue",
                    text="filing {} was amended by filing {} and multiple transaction matches were found for {}".format(amended_id, filing_id, transaction_id),
                    tags=["cnn-fec", "result:warning"])
            continue
        new_trans = new_trans[0]
        if new_trans.contributor_last_name != contributor_last_name:
            logging.log(title="donor reassignment issue",
                    text="Want to reassign transaction {} from filing {} to filing {} but last names mismatch: {}/{}".format(transaction_id, amended_id, filing_id, contributor_last_name, new_trans.contributor_last_name),    
                    tags=["cnn-fec", "result:warning"])
            continue

        new_trans.donor = transaction.donor
        new_trans.save()
        transaction.donor = None
        transaction.save()
        i += 1
    print("reassigned {} transactions from amended filing".format(i))



def clean_filing_fields(processed_filing, filing_fieldnames):
    #check whether the filing requires adding odd-year totals
    odd_filing = None
    addons = {}
    if processed_filing['form'] == 'F3X' and is_even_year(processed_filing):

        odd_filing = last_odd_filing(processed_filing)

    clean_filing = {}
    for k, v in processed_filing.items():
        key = k
        if k == 'col_a_cash_on_hand_beginning_period':
            key = 'cash_on_hand_beginning_period'
        elif k == 'col_a_cash_on_hand_close_of_period':
            key = 'cash_on_hand_close_of_period'
        elif k == 'col_a_debts_by_summary':
            key = 'debts_by_summary'
        elif k.startswith("col_a_"):
            key = "period_{}".format(k.replace('col_a_',''))
            
        elif k.startswith("col_b_"):
            key = "cycle_{}".format(k.replace('col_b_',''))
            if odd_filing and key in filing_fieldnames:
                addons[key] = getattr(odd_filing, key)

        if key in filing_fieldnames:
            if addons.get(key):
                sys.stdout.write('adding last odd cycle total for {}\n'.format(key))
                v = Decimal(v) + addons.get(key, Decimal(0))
            clean_filing[key] = v

        else:
            pass
    return clean_filing

def is_even_year(filing):
    try:
        year = int(filing['coverage_through_date'][0:4])
    except:
        sys.stdout.write('Could not find coverage date for filing {}, not fixing sums\n'.format(filing['filing_id']))
        return
    if year % 2 == 0:
        return True
    return False

def last_odd_filing(filing):
    committee_id = filing['filer_committee_id_number']
    committee_filings = Filing.objects.filter(filer_id=committee_id).order_by('-coverage_through_date','-date_signed')
    if len(committee_filings) == 0:
        return None
    for old_filing in committee_filings:
        if old_filing.coverage_through_date and int(old_filing.coverage_through_date[0:4]) == CYCLE-1:
            return old_filing


def evaluate_filing_file(filename, filing_id, myextra=None):
    if myextra:
        myextra=myextra.copy()
        myextra['FILING']=str(filing_id)
    form_line =''
    with open(filename, "r") as filing_csv:
        #pop each filing open, check the filing type, and add to queue if we want this one
        reader = csv.reader(filing_csv)
        #unreadable_files.readable_file_check('{}.csv'.format(filing_id),myextra=myextra)
        try:
            next(reader)
#        except UnicodeDecodeError:
#            with open(filename, encoding="cp1252") as filing_csv:
#                reader = csv.reader(filing_csv)
#                next(reader)
#                form_line = next(reader)
        except:
            #print('Filing has no lines!!')
            return False
        else:
            form_line = next(reader)
        if form_line[0].replace('A','').replace('N','') not in ACCEPTABLE_FORMS:
            create_or_update_filing_status(filing_id, 'REFUSED')
            #print('Not loading forms of type {}, refused this filing'.format(form_line[0]))
            return False
        if form_line[1] in BAD_COMMITTEES:
            create_or_update_filing_status(filing_id, 'REFUSED')
            #print('Not loading forms from committee {},refused this filing'.format(form_line[1]))
            return False

        #next, check if this filing has previously been refused
        if len(FilingStatus.objects.filter(filing_id=filing_id, status='REFUSED')) > 0:
            #print('We\'ve already refused this filing!')
            return False

        #next check if we already have the filing
        filings = Filing.objects.filter(filing_id=filing_id)
        if len(filings) == 0:
            return True
        if filings[0].status == 'FAILED':
            #delete the filing. it failed, so we're going to try again
            filings.delete()
            return True
        if filings[0].status == 'PROCESSING':
            #alert, but do not delete or reload.
            return False

        #if we get here, a filing exists, it's not 'failed' or 'processing' so we should not load
        return False

def get_filer_name(filer_id, myextra=None):
    #if we don't have a filer name, let's
    #1) search for the committee by id in our db
    #2) look it up by ID in the FEC's API and import a new committee
    committee = Committee.objects.filter(fec_id=filer_id)
    if len(committee) == 1 and committee[0].committee_name:
        return committee[0].committee_name
    if myextra:
        myextra=myextra.copy()
        myextra['COMMITTEE']=filer_id
    base_url = "https://api.open.fec.gov/v1/committee/{}/?api_key={}"
    url = base_url.format(filer_id, API_KEY)
    r = requests.get(url)
    try:
        data = r.json()
    except:
        logger.error('Failed to download valid JSON from FEC site while creating committee {}'.format(filer_id),
                               extra=myextra)
        return None
    #create the committee object
    try:
        comm = Committee.objects.create(
            fec_id=data['results'][0]['committee_id'],
            committee_name=data['results'][0]['name'],
            street_1=data['results'][0]['street_1'],
            street_2=data['results'][0]['street_2'],
            city=data['results'][0]['city'],
            state=data['results'][0]['state'],
            zipcode=data['results'][0]['zip'],
            committee_type=data['results'][0]['committee_type'],
            committee_designation=data['results'][0]['designation'],)
        comm.save()
        logger.info('Creating and saving new committee {}'.format(data['results'][0]['committee_id']),extra=myextra)
    except:
        logger.error('Failed to create and save committee {}'.format(filer_id),
                               extra=myextra)
        return None
    return data['results'][0]['name']

def load_filing(filing, filename, filing_fieldnames, myextra=None):
    #returns boolean depending on whether filing was loaded
    
    
    #this means the filing already exists
    #TODO add checking to see if import was successful
    if myextra:
        myextra=myextra.copy()
        myextra['FILING']=str(filing)
    filing_matches = Filing.objects.filter(filing_id=filing)
    if len(filing_matches) == 1:
        if filing_matches[0].status != "FAILED":
            logger.info('filing {} already exists\n'.format(filing), extra=myextra)
            return False
    
    #filing does not exist or it failed previously
    try:
        filing_dict = process_filing.process_electronic_filing(filename, dump_full=False)
    except Exception as e:
        logging.log(title="fec2json failed",
                    text="fec2json failed {} {}".format(filing, e),
                    tags=["cnn-fec", "result:fail"])
        return False

    #do not load filings outside of this cycle (these will likely be amendments of old filings)
    #we check this before we download the filing, but this seems like worth re-checking in case someone manually downloaded a file or something
    coverage_end = filing_dict.get('coverage_through_date')
    if not check_coverage_dates(filing_dict, coverage_end):
        #print('Not loading filings with end date {}'.format(coverage_end))
        create_or_update_filing_status(filing, 'REFUSED')
        return False

    #deal with amended filings
    is_amended = False
    amends_filing = None
    if filing_dict['amendment']:
        is_amended = True

        #oy, one filer really likes semi-colons.
        if filing_dict.get('amends_filing'):
            filing_dict['amends_filing'] = filing_dict['amends_filing'].replace(';','')
        try:
            amends_filing_str = filing_dict['amends_filing']
            amends_filing = int(amends_filing_str)
        except ValueError:
            #should be a warning or possibly critical
            logging.log(title="Filing {} Failed".format(filing),
                    text='Invalid amendment number {} for filing {}, creating filing and marking as FAILED\n'.format(filing_dict['amends_filing'],filing),
                    tags=["cnn-fec", "result:fail"])
            filing_obj = Filing.objects.create(filing_id=filing, status='FAILED')
            filing_obj.save()
            return False
        else:
            try:
                amended_filing = Filing.objects.filter(filing_id=amends_filing)[0]
            except IndexError:
                #if it's an F24 or F5, which don't always have coverage dates,
                #it is probably an amendment of an out-of-cycle filing
                #so do not load it
                if filing_dict['form'] in ['F24', 'F5']:
                    sys.stdout.write('Filing {} is an amended {} with no base. Probably from an old cycle. Not loading\n'.format(filing, filing_dict['form']))
                    create_or_update_filing_status(filing, 'REFUSED')
                    return False
                sys.stdout.write("could not find filing {}, which was amended by {}, so not deactivating any transactions\n".format(amends_filing, filing))
            else:
                #if there are filings that were amended by the amended filing
                #they also have to be deactivated, so look for them.
                other_amended_filings = Filing.objects.filter(amends_filing=amended_filing.filing_id).exclude(filing_id__gte=filing)
                amended_filings = [f for f in other_amended_filings] + [amended_filing]
                for amended_filing in amended_filings:
                    amended_filing.active = False
                    amended_filing.status = 'SUPERSEDED'
                    amended_filing.save()
                    ScheduleA.objects.filter(filing_id=amended_filing.filing_id).update(active=False, status='SUPERSEDED')
                    ScheduleB.objects.filter(filing_id=amended_filing.filing_id).update(active=False, status='SUPERSEDED')
                    ScheduleE.objects.filter(filing_id=amended_filing.filing_id).update(active=False, status='SUPERSEDED')
                    if myextra:
                        myextra=myextra.copy()
                        myextra['FILING']=str(amended_filing.filing_id)
                    logger.info("Filing {} was deactivated and status was set to SUPERSEDED because {} amends it".format(amended_filing.filing_id,filing), extra=myextra)

    if filing_dict['form'] in ['F3','F3X','F3P','F5']:
        #could be a periodic, so see if there are covered forms that need to be deactivated
        coverage_start_date = filing_dict['coverage_from_date']
        coverage_end_date = filing_dict['coverage_through_date']
        if coverage_start_date and coverage_end_date:
            #we're going to start by looking for whole forms to deactivate
            covered_filings = Filing.objects.filter(date_signed__gte=coverage_start_date,
                                                date_signed__lte=coverage_end_date,
                                                form__in=['F24','F5'],
                                                filer_id=filing_dict['filer_committee_id_number']).exclude(filing_id=filing) #this exclude prevents the current filing from being deactivated if it's already been saved somehow
            covered_filings.update(active=False, status='COVERED')
            covered_transactions = ScheduleE.objects.filter(filing_id__in=[f.filing_id for f in covered_filings])
            covered_transactions.update(active=False, status='COVERED')
            for f in covered_filings:
                if myextra:
                    myextra=myextra.copy()
                    myextra['FILING']=str(f.filing_id)
                logger.info("Filing {} was deactivated and status was set to COVERED because {} has overlapping coverage dates".format(f.filing_id,filing), extra=myextra)
            #there might be some additional transactions close to the edge of the filing period
            #that we should deactivate based on inconsistent dates inside filings
            individual_covered_transactions = ScheduleE.objects.filter(filer_committee_id_number=filing_dict['filer_committee_id_number'],
                                                                    active=True).exclude(filing_id=filing)
            by_expend_date = individual_covered_transactions.filter(expenditure_date__gte=coverage_start_date,
                                                                    expenditure_date__lte=coverage_end_date)
            by_expend_date.update(active=False, status='COVERED')
            for f in by_expend_date:
                if myextra:
                    myextra=myextra.copy()
                    myextra['FILING']=str(f.filing_id)
                    myextra['TRANSACTION']=f.transaction_id
                logger.info("SchedE transaction {} from filing {} was deactivated and status was set to COVERED because its expenditure_date is between {} and {} coverage dates of filing {}".format(f.transaction_id,f.filing_id,coverage_start_date,coverage_end_date,filing), extra=myextra)
            by_dissemination_date = individual_covered_transactions.filter(dissemination_date__gte=coverage_start_date,
                                                                    dissemination_date__lte=coverage_end_date)
            by_dissemination_date.update(active=False, status='COVERED')
            for f in by_dissemination_date:
                if myextra:
                    myextra=myextra.copy()
                    myextra['FILING']=str(f.filing_id)
                    myextra['TRANSACTION']=f.transaction_id
                logger.info("SchedE transaction {} from filing {} was deactivated and status was set to COVERED because its dissemination_date is between {} and {} coverage dates of filing {}".format(f.transaction_id,f.filing_id,coverage_start_date,coverage_end_date,filing), extra=myextra)


    clean_filing_dict = clean_filing_fields(filing_dict, filing_fieldnames)
    clean_filing_dict['filing_id'] = filing
    clean_filing_dict['filer_id'] = filing_dict['filer_committee_id_number']
    if filing_dict['form'] == 'F5':
        clean_filing_dict['period_independent_expenditures'] = filing_dict.get('total_independent_expenditure')
    person_punc = [',','','']
    person_namef = ['individual_last_name','individual_first_name','individual_middle_name']
    if filing_dict.get('committee_name') is None:
        clean_filing_dict['committee_name'] =  filing_dict.get('organization_name') or " ".join([filing_dict.get(n)+p for n,p in zip(person_namef,person_punc) if filing_dict.get(n)])
    if len(filing_matches) == 1:
        filing_matches.update(**clean_filing_dict)
        filing_obj = filing_matches[0]
        logger.info("Reloading {}, it failed previously".format(filing), extra=myextra)
    else:
        filing_obj = Filing.objects.create(**clean_filing_dict)
        logger.info("Creating and saving new filing {}".format(filing), extra=myextra)
    filing_obj.save()

    #create or update committee
    if filing_dict.get('committee_name') is None:
        filing_obj.committee_name = get_filer_name(filing_dict['filer_committee_id_number'],myextra=myextra)
        filing_obj.save()

    fec_id=filing_dict['filer_committee_id_number']
    if myextra:
        myextra['COMMITTEE']=fec_id
    try:
        comm = Committee.objects.create(fec_id=filing_dict['filer_committee_id_number'])
        comm.save()
        logger.info('Creating and saving new committee {} from filing {}'.format(fec_id,filing),extra=myextra)
    except:
        #committee already exists
        pass

    try:
        committee_fieldnames = [f.name for f in Committee._meta.get_fields()]
        committee = {}
        committee['zipcode'] = filing_dict['zip']
        fields_count = 1
        for fn in committee_fieldnames:
            try:
                field = filing_dict[fn]
            except:
                continue
            committee[fn] = field
            fields_count += 1

        comm = Committee.objects.filter(fec_id=filing_dict['filer_committee_id_number']).update(**committee)
        message = lambda x: '{} column{} {} updated.'.format(x, pluralize(x), pluralize(x, 'was,were'))
        logger.info('Updating committee {} from filing {}, {}'.format(fec_id,filing,message(fields_count)),extra=myextra)
    except:
        logger.warning('Failed to update committee {}'.format(fec_id),
                               extra=myextra)

    #add itemizations - eventually we're going to need to bulk insert here
    #skedA's
    try:
        scha_count = 0
        schb_count = 0
        sche_count = 0
        if 'itemizations' in filing_dict:
            load_chunk_size = 20000
            complete = False
            while not complete:
                i = 0
                itemization_dict = {}
                while i < load_chunk_size:
                    try:
                        line = next(filing_dict['itemizations'])
                        i += 1
                    except StopIteration:
                        complete = True
                        break
                    #print(line)
                    itemization_type = process_filing.get_itemization_type(line.get('form_type'))
                    if itemization_type not in itemization_dict:
                        itemization_dict[itemization_type] = []
                    itemization_dict[itemization_type].append(line)

                if 'SchA' in itemization_dict:
                    scha_count += load_itemizations(ScheduleA, itemization_dict['SchA'])
                if 'SchB' in itemization_dict:
                    schb_count += load_itemizations(ScheduleB, itemization_dict['SchB'])
                if 'SchE' in itemization_dict:
                    sche_count += load_itemizations(ScheduleE, itemization_dict['SchE'])
                if 'F57' in itemization_dict:
                    sche_count += load_itemizations(ScheduleE, itemization_dict['F57'])
            logger.info("inserted {} schedule A's\n".format(scha_count), extra=myextra)
            logger.info("inserted {} schedule B's\n".format(schb_count), extra=myextra)
            logger.info("inserted {} schedule E's\n".format(sche_count), extra=myextra)

    except:
        #something failed in the transaction loading, keep the filing as failed
        #but remove the itemizations
        filing_obj.status='FAILED'
        filing_obj.save()
        create_or_update_filing_status(filing, 'FAILED')
        ScheduleA.objects.filter(filing_id=filing).delete()
        ScheduleB.objects.filter(filing_id=filing).delete()
        ScheduleE.objects.filter(filing_id=filing).delete()
        if myextra:
            myextra['TAGS']='cnn-fec, result:fail'
        logger.error("Itemization load failed, marking {} as FAILED".format(filing),
                    extra=myextra)
        return False

    if is_amended and amends_filing:
        reassign_standardized_donors(filing, amends_filing)

    #add IE total to f24s
    if filing_obj.form == 'F24':
        ies = ScheduleE.objects.filter(filing_id=filing, active=True)
        filing_obj.computed_ie_total_for_f24 = sum([ie.expenditure_amount for ie in ies])




    sys.stdout.write('Marking {} as ACTIVE\n'.format(filing))
    filing_obj.status='ACTIVE'
    filing_obj.save()
    create_or_update_filing_status(filing, 'SUCCESS')

    return True

def create_or_update_filing_status(filing_id, status):
    fs = FilingStatus.objects.filter(filing_id=filing_id)
    if len(fs) > 0:
        fs = fs[0]
        fs.status = status
        fs.save()
    else:
        fs = FilingStatus.objects.create(filing_id=filing_id, status=status)
        fs.save()    


def load_filings(filing_dir, myextra=None):

    
    filing_fieldnames = [f.name for f in Filing._meta.get_fields()]

    filing_csvs = sorted(os.listdir(filing_dir))
    filings_loaded = 0
    for filename in filing_csvs:
        filing_id = filename.split(".")[0]
        if filename[0] == ".":
            continue
        if myextra:
            myextra=myextra.copy()
            myextra['FILING']=filing_id
        try:
            int(filing_id)
        except:
            logging.log(title="Bad FEC filename",
                    text='did not recognize filing {}'.format(filename),
                    tags=["cnn-fec", "result:warn"])
            myextra['TAGS']="cnn-fec", "result:warn"
            logger.warn('Bad FEC filename {}'.format(filename),extra=myextra)
            continue

        full_filename = "{}{}".format(filing_dir, filename)
        
        if not evaluate_filing_file(full_filename, filing_id):
            continue
                
        logger.info("Started filing {}".format(filing_id),extra=myextra)
        

        if load_filing(filing_id, full_filename, filing_fieldnames):

            logging.log(title="Filing {} loaded".format(filing_id),
                    text='filing {} successfully loaded'.format(filing_id),
                    tags=["cnn-fec", "result:success"])

            filings_loaded += 1

    if myextra:
        myextra['FILINGS_LOADED']=filings_loaded
        myextra['TAGS']="cnn-fec", "result:success"
    logger.info("{} filings successfully loaded".format(filings_loaded),extra=myextra)