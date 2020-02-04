import os, sys
import logging
from cycle_2020.models import FilingStatus

LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
logger = logging.getLogger("cnn-fec."+__name__)
logger.setLevel(LOGLEVEL)

filing_dir="filings/"

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
    if not os.path.isfile(filename):
        logger.info("File {} doesn't exist".format(filename),extra=myextra)
        return False
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

def delete_file(filing_id, filing_dir=filing_dir, myextra=None):
    """delete a downloaded file.

        Args:
            filing_id (int): A numbered FEC filing_id, for example '123456'.
            filing_dir (str, optional): An absolute directory path for the filing, defaults
                to a 'filings' directory under the project root.

        Returns:
            True if the filing is deleted or it doesn't find the filing,
                Logs details of results if LOGLEVEL has been set to 'info'. Logs deletion errors. Logs warning if the path isn't found.
    """
    filename = '{}{}.csv'.format(filing_dir, filing_id)
    if myextra:
        myextra=myextra.copy()
        myextra['FILING']=filing_id
    if os.path.isfile(filename):
        try:
            os.unlink(filename)
            logger.info('{}.csv deleted'.format(filing_id),extra=myextra)
        except Exception as err:
            logger.error('Error deleting {}'.format(filename),extra=myextra)
            raise err
    else:
        logger.warn('Filing {} not found in {}'.format(filing_id,filing_dir),extra=myextra)
    return True
