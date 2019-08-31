import os, sys
import logging
from cycle_2020.models import FilingStatus

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logger = logging.getLogger("cnn-fec."+__name__)
logger.setLevel(LOGLEVEL)

filing_dir = os.environ.get('HOME') + '/scripts/cnn-fec/filings/'

def readable_file_check(file, filing_dir=filing_dir, myextra=None):
    """pop open a downloaded file and flag it if it's not a readable csv.

        Args:
            file (str): A numbered FEC csv file, for example '123456.csv'.
            filing_dir (str, optional): An absolute directory path for the file, defaults
                to a 'filings' directory under the project root.

        Returns:
            True if the filing can be opened and read and doesn't appear to be a webpage,
                False otherwise. Logs details of False results if LOGLEVEL has been set to 'info'.
    """
    filename = '{}{}'.format(filing_dir, file)
    if myextra:
        myextra=myextra.copy()
        myextra['FILING']=file.split('.')[0]
    else:
        myextra=''
    #with open(filename, errors="backslashreplace") as f:
    with open(filename) as f:
        try:
            if f.readlines(1)[0] == '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n':
                logger.info("File {} isn't a csv, FEC site returned an empty web page instead".format(file),extra=myextra)
                return False
            else:
                return True
        except UnicodeDecodeError:
            logger.info("File {} can't be decoded".format(file),extra=myextra)
            return False
        except IndexError:
            if file == '.placeholder':
                logger.debug("Skipping {}, not a filing".format(file),extra=myextra)
                return True
            else:
                logger.info("File {} can't be indexed".format(file),extra=myextra)
                return False

def delete_file(file, filing_dir=filing_dir, myextra=None):
    filename = '{}{}.csv'.format(filing_dir, file)
    if myextra:
        myextra=myextra.copy()
        myextra['FILING']=file.split('.')[0]
    else:
        myextra=''
    if os.path.isfile(filename):
        try:
            os.unlink(filename)
            logger.info('{}.csv deleted'.format(file),extra=myextra)
        except Exception as err:
            logger.error('Error deleting {}'.format(filename),extra=myextra)
            raise err
    return True

def reset_refused_filing_to_failed(filing_id, myextra=None):
    if myextra:
        myextra=myextra.copy()
        myextra['FILING']=filing_id
    else:
        myextra=''
    try:
        fs = FilingStatus.objects.filter(filing_id=filing_id)
        if len(fs) > 0:
            fs = fs[0]
            if fs.status == 'REFUSED':
                fs.status = 'FAILED'
                fs.save()
                logger.info('Filing {} status updated to FAILED'.format(filing_id),extra=myextra)
        return True
    except Exception as err:
        logger.error("Filing {} status can't be reset".format(file),extra=myextra)
        raise err

def recheck_existing_files(filing_dir=filing_dir, myextra=None):
    #find unreadable files, reset their status if we've refused them and delete them
    try:
        existing_files = sorted(os.listdir(filing_dir))
        retry_filings = set()
        filecounter = 0
        for file in existing_files:
            filecounter += 1
            if filecounter % 10000 == 0 or filecounter == len(existing_files):
                logger.debug('{} of {} files, found {} unreadable files'.format(filecounter,len(existing_files),len(retry_filings)),extra=myextra)
            if not readable_file_check(file, filing_dir=filing_dir, myextra=myextra):
                #if reset_refused_filing_to_failed(filing_id):
                #    if delete_file(file, filing_dir=filing_dir):
                        retry_filings.add(file.split('.')[0])
        return retry_filings
    except Exception as err:
        logger.critical("File recheck failed!",extra=myextra)
        raise err
