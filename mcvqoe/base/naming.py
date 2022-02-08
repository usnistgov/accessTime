
import os.path
import re

repocess_detect = r'(?P<reprocess>R)?'
base_start = r'(?P<base>capture2?_'
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

def match_name(name, re_type="universal", raise_error=True):
    """
    Return a match object for a test filename.

    Match name with one of the regular expressions and return the match object.

    Parameters
    ----------
    name : str
        The name of the measurement file. This can be a fully qualified path or
        just the name of the file.

    re_type : str, default="universal"
        The type of re to use for the match. Currently the only valid values are
        "universal" (default) and "access_csv". Universal should match any name.
        While access_csv will only match access time csv files that contain a
        clip name.

    Returns
    -------
    match object
        The match object for the filename.

    Raises
    ------
    RuntimeError
        If the file name could not be matched.

    KeyError
        If an invalid `re_type` is passed.

    """
    name = _normalize(name)

    m = re.match(match_res[re_type], name)

    if not m and raise_error:
        raise RuntimeError(f'Unable to get base name from \'{name}\'')

    #return match object
    return m

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

    re_type : str, default="universal"
        The type of re to use for the match. Currently the only valid values are
        "universal" (default) and "access_csv". Universal should match any name.
        While access_csv will only match access time csv files that contain a
        clip name.

    Returns
    -------
    str
        The base name of the file.

    Raises
    ------
    RuntimeError
        If the file name could not be matched.

    KeyError
        If an invalid `re_type` is passed.
    """

    m = match_name(name, re_type=re_type)

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

    m = match_name(name, re_type="access_csv")

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

    m = match_name(name)

    return "_".join(m.group('date','time'))