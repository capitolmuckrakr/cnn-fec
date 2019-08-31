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

        myextra = {'MESSAGE_ID':myid,'SYSLOG_IDENTIFIER':SYSLOG_IDENTIFIER}

        filings = unreadable_files.recheck_existing_files(filing_dir,myextra=myextra)
        
        if  len(filings) >0:
            myextra=myextra.copy()
            myextra['TAGS']='cnn-fec, result:success'
            logger.info("Found and deleted {} unreadable files".format(len(filings)),extra=myextra)

        
        #loader.download_filings(filings, filing_dir,extra=myextra)
        #loader.load_filings(filing_dir)


