import pytz
import datetime
import os
import requests
import csv
import process_filing
import time
import traceback
import sys

from cycle_2020.utils import unreadable_files

from cycle_2020.utils import loader

from django.core.management.base import BaseCommand, CommandError

import logging, uuid

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
SYSLOG_IDENTIFIER = os.environ.get('SYSLOG_IDENTIFIER','')
logger = logging.getLogger("cnn-fec."+__name__)
logger.setLevel(LOGLEVEL)

myid=uuid.uuid4()

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--filing_dir',
            dest='filing_dir',
            help='where to save and read filings from')
    #default is to do 

    def handle(self, *args, **options):
        
        if options['filing_dir']:
            filing_dir = options['filing_dir']
        else:
            filing_dir = os.environ.get('HOME') + '/scripts/cnn-fec/filings/'

        filings = unreadable_files_2020.recheck_existing_files(filing_dir)
        x = {'MESSAGE_ID':myid,'SYSLOG_IDENTIFIER':SYSLOG_IDENTIFIER,'TAGS':'cnn-fec, result:success'}
        if  len(filings) >0:
            logger.warning("Found and deleted {} unreadable files".format(len(filings)),extra=x)

        
        #loader.download_filings(filings, filing_dir)
        #loader.load_filings(filing_dir)


