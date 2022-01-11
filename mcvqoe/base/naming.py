
import os.path
import re

repocess_detect = r'(?P<reprocess>R)?'
base_start = r'(?P<base>capture+_'
test_type = r'(?P<type>.*)'
timestamp = r'_(?P<date>\d{2}-[A-z][a-z]{2}-\d{2,4})_(?P<time>\d{2}-\d{2}-\d{2})'
access_word = r'_(?P<clip>(?P<talker>[MF]\d)_b(?P<batch>\d+)'\
              r'_w(?P<word>\d)_(?P<cname>[a-z]+))'
suffix = r'(?:_(?P<suffix>BAD|TEMP))?'

match_res = {
                "universal" : repocess_detect +
                              base_start + test_type + timestamp + ')' +
                              '(?:' + access_word + ')?' + suffix,
                "access_csv" : repocess_detect +
                               base_start + test_type + timestamp + ')' +
                               access_word + suffix,
            }

def _normalize(name):
    #check for empty
    if not name:
        raise RuntimeError(f'Unable to get base name from empty string')
    #strip off any path components
    dirname, basename = os.path.split(name)
    #check
    if not basename:
        #name must have ended with a separator
        #get the last path component
        return os.path.basename(dirname)
    else:
        return basename


def get_meas_basename(name, re_type="universal"):
    """
    Get the base name for the measurement.

    This returns the base name for a given file name, stripping off any reprocess
    prefix, access time name, or suffix.

    Parameters
    ----------
    name : str
        The name of the measurement file. This can be a fully qualified path or
        just the name of the file.

    Returns
    -------
    str
        The base name of the file.

    Raises
    ------
    RuntimeError
        If the file name could not be matched.
    """

    name = _normalize(name)

    m = re.match(match_res[re_type], name)

    if not m:
        raise RuntimeError(f'Unable to get base name from \'{name}\'')

    return m.group('base')

def get_access_clip_info(name):
    """
    Get access time clip information from filename

    Return the talker, batch word and clip name given an access time csv name.

    Parameters
    ----------
    name : str
        The name of access time csv file. This can be a fully qualified path or
        just the name of the file.

    Returns
    -------
    talker : str
        The talker name from the file.
    batch : int
        The batch number for the file.
    word : int
        The word number for the file.
    cname : str
        The clip name for the file.

    Raises
    ------
    RuntimeError
        If the filename could not be matched.
    """
    name = _normalize(name)

    m = re.match(match_res["access_csv"], name)

    if not m:
        raise RuntimeError(f'Unable to get access info from \'{name}\'')

    return m.group("talker"), int(m.group("batch")), int(m.group("word")), m.group("cname")

def get_meas_date_str(name):
    """"
    Extract date/time from measurement file name.

    Parameters
    ----------
    name : str
        The file name of the measurement. This can be a fully qualified path or
        just the name of the file.

    Returns
    -------
    str
        The date portion of the filename.

    Raises
    ------
    RuntimeError
        If the file name could not be matched.
    """

    name = _normalize(name)

    m = re.match(match_res["universal"], name)

    if not m:
        raise RuntimeError(f'Unable to get date from \'{name}\'')

    return "_".join(m.group('date','time'))