# coding: utf-8
from cycle_2020.utils import loader
import os, logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.WARNING)
stream_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(stream_format)
filing_dir = os.environ.get('HOME') + '/scripts/cnn-fec/filings/'

def bad_file_check(file,  filing_dir=filing_dir):
    #pop open a downloaded file and flag it if it's not a readable csv
    filename = '{}{}'.format(filing_dir, file)
    #with open(filename, errors="backslashreplace") as f:
    with open(filename) as f:
        try:
            if f.readlines(1)[0] == '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n':
                return False
            else:
                return True
        except UnicodeDecodeError:
            logger.warning("File {} can't be decoded".format(file))
            return False
        except IndexError:
            logger.warning("File {} can't be indexed".format(file))
            return False
    filename = None

def recheck_existing_filings(filing_dir=filing_dir):
    #find bad filings
    existing_filings = os.listdir(filing_dir)
    retry_filings = set()
    filecounter = 0
    for file in existing_filings:
        filecounter += 1
        if filecounter % 10000 == 0:
            logger.info('{} of {} files, found {} bad files'.format(filecounter,len(existing_filings),len(retry_filings)))
        if not bad_file_check(file, filing_dir=filing_dir):
            retry_filings.add(file.split('.')[0])
    return retry_filings

def delete_bad_files(filings, filing_dir=filing_dir):
    for filing_id in filings:
        filename = '{}{}.csv'.format(filing_dir, filing_id)
        if os.path.isfile(filename):
            try:
                os.unlink(filename)
            except:
                logger.error('Error deleting {}'.format(filename))
                return False
            try:
                loader.create_or_update_filing_status(filing_id,'FAILED')
            except:
                logger.error('Error updating status of filing {}'.format(filing_id))
                return False
    return True
        
if __name__ == '__main__':
    bad_files = recheck_existing_filings(filing_dir)
    delete_bad_files(bad_files, filing_dir)
    loader.download_filings(bad_files, filing_dir)
