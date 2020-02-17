import pytz
import datetime

def date_validation(datestr):
    fec_time=pytz.timezone('US/Eastern')
    limit = int((datetime.datetime.now(fec_time) + datetime.timedelta(days=365)).strftime('%Y%m%d'))
    try:
        if limit > int(datestr) > 20161108:
            return True
    except:
        pass
    return False