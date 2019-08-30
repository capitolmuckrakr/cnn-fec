import pytz
import datetime
import os
import requests
import csv
import process_filing
import time
import traceback
import sys

from cycle_2020.models import *

from cycle_2020.utils import loader

from django.core.management.base import BaseCommand, CommandError

import logging, uuid

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
SYSLOG_IDENTIFIER = os.environ.get('SYSLOG_IDENTIFIER','')
logger = logging.getLogger("cnn-fec."+__name__)
logger.setLevel(LOGLEVEL)

myid=uuid.uuid4()

myextra = {'MESSAGE_ID':myid,'SYSLOG_IDENTIFIER':SYSLOG_IDENTIFIER}

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--filing_dir',
            dest='filing_dir',
            help='where to save and read filings from')
    #default is to do past two days

    def handle(self, *args, **options):
        
        fec_time=pytz.timezone('US/Eastern') #fec time is eastern

        unparsed_start = datetime.datetime.now(fec_time) - datetime.timedelta(days=2)
        start_date = unparsed_start.strftime('%Y%m%d')
        unparsed_end = datetime.datetime.now(fec_time) + datetime.timedelta(days=1)
        end_date = unparsed_end.strftime('%Y%m%d')
        if options['filing_dir']:
            filing_dir = options['filing_dir']
        else:
            filing_dir = 'filings/'

        logger.info("looking for filings for period {}-{}".format(start_date, end_date), extra=myextra)
        filings = loader.get_filing_list(start_date, end_date, extra=myextra)
        if not filings:
            logger.warning("failed to find any filings for period {}-{}".format(start_date, end_date), extra=myextra)

        
        #loader.download_filings(filings, filing_dir, extra=myextra)
        #loader.load_filings(filing_dir,extra=myextra)


