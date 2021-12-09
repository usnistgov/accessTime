#!/usr/bin/env python

# file operations and directory listing
import os

# used for * filename expansions
import glob

# used for copy function
import shutil

# argument parsing
import argparse

# file time parsing
import datetime

# for configuration file reading
import configparser

# prefix to show that this path needs sub folders copied
recur_prefix = "*"

# prefix to show not to backup sync folder
noback_prefix = "-"

def terminal_progress_update(
            prog_type,
            total,
            current,
            **kwargs):
    indents = {
        'main' : 0,
        'sub' : 1,
        'cull' : 1,
        'log' : 1,
        'subsub' : 2,
        'skip' : 1,
        'supdate' : 0,
        }

    split_type = prog_type.split('-')

    major_type = split_type[0]

    if len(split_type) > 1:
        minor_type = split_type[1]
    else:
        #no minor type
        minor_type = None

    if major_type in indents:
        num = indents[major_type]
        if major_type == prog_type:
            num -=1

        indent = '\t' * num
    else:
        indent = ''

    if prog_type == 'main' :
        print(indent+f'processing directory {current} of {total}')
    if prog_type == 'main-section' :
        print(indent+f'Running section {kwargs["sect"]}')
    if prog_type == 'log-complete':
        if kwargs['lines']:
            print(f'{kwargs["lines"]} lines copied')
        else:
            print("Log files are identical, no lines copied")
        # print success message
        print(f'Log updated successfully to {kwargs["file"]}\n')
    elif prog_type == 'sub' :
        print(indent+f'processing subdirectory {current} of {total}')
    #common things
    elif minor_type == 'start':
        print(indent+f'Found {total} files to copy')
    elif minor_type == 'update':
        #only update terminal for subsub
        if major_type == 'subsub' :
            if current % 100 ==0:
                print(indent+f'copying file {current} of {total}')
    elif minor_type == 'dir':
        if major_type == 'log':
            print(indent+f'Finding Log files in \'{kwargs["dir"]}\'')
        else:
            print(indent+f'Checking directory \'{kwargs["dir"]}\' for new files')
    elif minor_type == 'skip':
        if 'dir' in kwargs:
            print(indent + f'No new files found to copy to \'{kwargs["dir"]}\'')
        else:
            print(indent + 'Up to date')
    elif minor_type == 'backup':
        print(indent + f'Backing files up from \'{kwargs["dest"]}\' to \'{kwargs["src"]}\'')
    elif minor_type == 'invalid':
        print(indent + f'Skipping \'{kwargs["dir"]}\' it is not a directory or .zip file')
    elif minor_type == 'new':
        print(indent+f'Creating folder \'{kwargs["dir"]}\'')
    elif minor_type == 'temp':
        print(indent+f'Skipping \'{kwargs["file"]}\'')
    elif minor_type == 'skipdir':
        print(indent+f'Skipping Directory \'{kwargs["dir"]}\'')
    elif minor_type == 'srcdest':
        print(indent + f'Copying \'{kwargs["src"]}\' to \'{kwargs["dest"]}\'')
    #cull things
    elif prog_type == 'cull-deldir':
        print(indent + f'Deleting old directory \'{kwargs["dir"]}\'')
    elif prog_type == 'cull-delfile':
        print(indent + f'Deleting old directory \'{kwargs["file"]}\'')
    elif prog_type == 'cull-baddate' :
        print(indent + f'Unable to parse date in file \'{kwargs["file"]}\'')
    #skipping things
    elif prog_type == 'skip-later' :
        print(indent+f'Skipping {kwargs["file"]} for later')
    elif prog_type == 'skip-start' :
        #ignore indent here, this will be done at the end
        print(f'Copying skipped {kwargs["ext"]} files')
    elif prog_type == 'supdate-old':
        print("Sync version old, updating")
    elif prog_type == 'supdate-vmissing':
        print("Sync version missing, updating")
    elif prog_type == 'supdate-missing':
        print("Sync directory not found, updating")

# data directory names
data_dirs = (
    # 1 location data/processed data folder
    os.path.join("data", "csv"),
    recur_prefix + os.path.join("data", "wav"),
    # 2 location tx and rx raw data folders
    os.path.join("data", "2loc_rx-data"),
    recur_prefix + os.path.join("data", "2loc_tx-data"),
    # recovery and error
    os.path.join("data", "recovery"),
    os.path.join("data", "error"),
    # legacy .mat files
    noback_prefix + "data_matfiles",
)

# class to copy directories and skip some files
class cpyDelay:
    def __init__(self, ext, **kwargs):
        # initialize list of skipped files
        self.skip_list = []
        self.dly_ext = ext
        self.verbose = 0
        self.progress_update = terminal_progress_update

        #get properties from kwargs
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise TypeError(f"{k} is not a valid keyword argument")

    def ignore_func(self, src, dest):
        def _ignore(path, names):
            # get relative path into src directory
            relpath = os.path.relpath(path, src)

            # set of names to ignore
            ignore = set()
            # look at all names to see if they should be ignored
            for n, name in enumerate(names):
                # get extension
                (_, ext) = os.path.splitext(name)
                # check if extension should be ignored
                if ext == self.dly_ext:
                    # add file to list to ignore
                    ignore.add(name)
                    # construct full filenames to save for later
                    full_src = os.path.join(path, name)
                    full_dst = os.path.join(dest, relpath, name)
                    # add to list
                    self.skip_list.append((full_src, full_dst))
                    if self.verbose:
                        # give update
                        self.progress_update('skip-later', 0, 0, file=full_src)
            # return files found to ignore
            return ignore

        # return function to be used for ignore with copytree
        return _ignore

    def copytree(self, src, dest, **kwargs):
        # call copytree with ignore function
        shutil.copytree(src, dest, ignore=self.ignore_func(src, dest), **kwargs)

    def copy_skipped(self):
        # get number of files to copy
        total = len(self.skip_list)
        # notify user of delayed copies
        self.progress_update('skip-start', total, 0, ext=self.dly_ext)
        # loop through skipped files
        for n, (src, dest) in enumerate(self.skip_list):
            self.progress_update('skip-copy', total, n, src=src, dest=dest)
            shutil.copy2(src, dest)
        # clear out skip_list
        skip_list = []


class TestSyncer:
    def __init__(self, **kwargs):
        #set default values
        self.progress_update=terminal_progress_update
        self.bd=True
        self.cull=False
        self.sunset=30
        self.thorough=False
        self.copied_files = set()

        #get properties from kwargs
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)
            else:
                raise TypeError(f"{k} is not a valid keyword argument")

        # create object to skip .zip files with
        self.skip_zip = cpyDelay(".zip", verbose=True, progress_update=self.progress_update)

    def _dir_cpy(self, src, dest):
        # update progress
        self.progress_update('subsub-dir', 0, 0, dir=src)
        # set of files in source directory
        sset = set(os.listdir(src))
        # create dest if it does not exist
        os.makedirs(dest, exist_ok=True)
        # set of files in the destination directory
        dset = set(os.listdir(dest))
        # get the files that are not in dest
        cpy = sset.difference(dset)
        # find number of files to copy
        cnum = len(cpy)
        # check if we have files to copy
        if cnum:
            self.progress_update('subsub-start', cnum, 0)
            for count, f in enumerate(cpy, 1):
                # update progress
                self.progress_update('subsub-update', cnum, count)
                # create source and destination names
                sname = os.path.join(src, f)
                dname = os.path.join(dest, f)
                # copy file
                shutil.copyfile(sname, dname)
                # copy metadata
                shutil.copystat(sname, dname)

        else:
            self.progress_update('subsub-skip', 0, 0, dir=src)


    # function to copy unique files
    def sync_files(self, spath, dpath):
        # get datetime object for current time
        current_time = datetime.datetime.now()

        # loop over files in data_dirs
        for dat in data_dirs:
            # check for directory of directory path
            if dat.startswith(recur_prefix):
                recur = True
                # strip recur prefix from name
                dat_d = dat[len(recur_prefix) :]
            elif dat.startswith(noback_prefix):
                recur = False
                # strip recur prefix from name
                dat_d = dat[len(noback_prefix) :]
            else:
                recur = False
                dat_d = dat
            # construct source name
            src = os.path.join(spath, dat_d)
            # check if source dir exists
            if os.path.exists(src):
                self.progress_update('sub-dir', 0, 0, dir=src)
                # set of files in source directory
                sset = set(os.listdir(src))
                # construct destination name
                dest = os.path.join(dpath, dat_d)
                # check if directory name exists and source directory has files
                if sset and not os.path.exists(dest):
                    self.progress_update('sub-new', 0, 0, dir=dest)
                    # create folder
                    os.makedirs(dest, exist_ok=True)
                if os.path.exists(dest):
                    # set of files in the destination directory
                    dset = set(os.listdir(dest))
                else:
                    # empty set for dest
                    dset = set()
                # check if we are decending into directories
                if recur and self.thorough:
                    # yes, copy everything
                    # we will work out which files in subfolders to copy later

                    #get total number of dirs to check
                    cnum = len(sset)
                    for n, dir in enumerate(sset):
                        self.progress_update('sub-update', cnum, n, dir=sname)
                        # create source and destination names
                        sname = os.path.join(src, dir)
                        dname = os.path.join(dest, dir)
                        # check if this is a directory
                        if os.path.isdir(sname):
                            # yes, copy with dir_cpy
                            self._dir_cpy(sname, dname)
                            self.copied_files.add(os.path.basename(dname))
                        else:
                            # no, check extension
                            _, ext = os.path.splitext(sname)
                            # ignore case by lowering
                            ext = ext.lower()
                            # is this a zip file?
                            if ext == ".zip":
                                # yes, copy it
                                shutil.copyfile(sname, dname)
                                # and its metadata
                                shutil.copystat(sname, dname)
                                # add copied file name to set
                                simple_name, _ = os.path.splitext(os.path.basename(dname))
                                self.copied_files.add(simple_name)
                            else:
                                # no, give message
                                self.progress_update('sub-invalid', cnum, n, dir=sname)

                else:
                    # get the files that are not in dest
                    cpy = sset.difference(dset)
                    # check if there are files to copy
                    if cpy:
                        #get number of files to copy
                        cnum=len(cpy)
                        # copy files from src to dest that are not in dest
                        for n, f in enumerate(cpy):
                            #update progress
                            self.progress_update('sub-update', cnum, n, file=f)
                            # check for temp files
                            if f.endswith("TEMP.mat"):
                                self.progress_update('sub-temp', cnum, n, file=f)
                                # skip this file
                                continue
                            # create source and destination names
                            sname = os.path.join(src, f)
                            dname = os.path.join(dest, f)
                            # progress update with source and destination
                            self.progress_update('sub-srcdest', cnum, n, src=sname, dest=dname)
                            if recur and os.path.isdir(sname):
                                # copy directory
                                self.skip_zip.copytree(sname, dname)
                                # TODO: copy metadata?
                            else:
                                # copy file
                                shutil.copyfile(sname, dname)
                                # copy metadata
                                shutil.copystat(sname, dname)
                                # add copied file name to set
                                simple_name, _ = os.path.splitext(os.path.basename(dname))
                                self.copied_files.add(simple_name)
                    else:
                        self.progress_update('sub-skip', 0, 0, dir=dest)

                # check if we need to copy in the reverse
                if self.bd and not dat.startswith(noback_prefix):
                    # get the files that are not in src
                    cpy = dset.difference(sset)
                    # check if there are files to copy
                    if cpy:
                        # get number of files
                        cnum = len(cpy)
                        self.progress_update('sub-backup', cnum, 0, file=f)
                        # copy files from dest to src that are not in src
                        for n, f in enumerate(cpy):
                            self.progress_update('sub-update', cnum, n)
                            # check for temp files
                            if f.endswith("TEMP.mat"):
                                # print a message
                                self.progress_update('sub-temp', cnum, n, file=f)
                                # skip this file
                                continue
                            # create source and destination names
                            sname = os.path.join(dest, f)
                            dname = os.path.join(src, f)
                            # check if source is a directory
                            if not recur and os.path.isdir(sname):
                                # print a message
                                self.progress_update('sub-skipdir', cnum, n, dir=sname)
                                # skip this file
                                continue
                            # update progress
                            self.progress_update('sub-srcdest', cnum, n, src=sname, dest=dname)
                            if recur:
                                # copy directory
                                self.skip_zip.copytree(sname, dname)
                                # TODO: copy metadata?
                            else:
                                # copy file
                                shutil.copyfile(sname, dname)
                                # copy metadata
                                shutil.copystat(sname, dname)
                elif self.cull:
                    #get number of files
                    cnum=len(sset)
                    # find old files and delete them
                    for n, f in enumerate(sset):
                        self.progress_update('cull-update', cnum, n)
                        # strip extension off of name
                        name, ext = os.path.splitext(f)
                        # split name into parts
                        parts = name.split("_")
                        num_pts = len(parts)
                        # check extension
                        if ext == ".mat":
                            if parts[-1] in ("ERROR", "TEMP"):
                                date_slice = slice(num_pts - 3, num_pts - 1)
                            elif parts[-2] == "of":
                                date_slice = slice(num_pts - 5, num_pts - 3)
                            else:
                                date_slice = slice(num_pts - 2, num_pts)
                        elif ext == ".csv":
                            date_slice = slice(num_pts - 6, num_pts - 4)
                        else:
                            date_slice = date_slice = slice(num_pts - 2, num_pts)
                        # grab date from filename
                        dstr = "_".join(parts[date_slice])
                        try:
                            # parse string
                            f_date = datetime.datetime.strptime(dstr, "%d-%b-%Y_%H-%M-%S")
                            # calculate file age
                            age = current_time - f_date
                            # check if file is older than sunset days
                            if age.days > self.sunset:
                                # create file name
                                fullname = os.path.join(src, f)
                                # check for directory
                                if os.path.isdir(fullname):
                                    # print message
                                    self.progress_update('cull-dir', cnum, n, dir=fullname)
                                    shutil.rmtree(fullname)
                                else:
                                    # print message
                                    self.progress_update('cull-file', cnum, n, file=fullname)
                                    # delete file
                                    os.remove(fullname)
                        except ValueError:
                            self.progress_update('cull-baddate', cnum, n, file=os.path.join(src, f))

    def finish_tasks(self):
        # copy .zip files that we skipped earlier
        self.skip_zip.copy_skipped()

def export_sync(config_name, progress_update=terminal_progress_update, **kwargs):

    #don't allow cull to be used here
    if 'cull' in kwargs and kwargs['cull']:
        raise TypeError('cull is not supported for export_sync')

   # create a config parser
    config = configparser.ConfigParser()

    # load config file
    config.read(config_name)

    if not config.sections():
        raise ValueError(f"Configuration file not found at {config_name}.")

    # find configuration file location, all paths are relative to this
    config_fold = os.path.dirname(os.path.abspath(config_name))

    #create a sync object
    sync_obj = TestSyncer(**kwargs)

    #get number of sections
    snum = len(config.sections())

    for n, section in enumerate(config.sections()):
        # print section message
        progress_update('main-section', snum, n, sect=section)

        # get, what should be, the relative path from config
        src_rel = config[section]["src"]

        if os.path.isabs(src_rel):
            raise RuntimeError("source paths must not be absolute paths")

        # make path absolute
        src_dir = os.path.normpath(os.path.join(config_fold, src_rel))

        # print log files message
        progress_update('log-dir', 0, 0, dir=src_dir)
        # list log files
        logs = glob.glob(os.path.join(src_dir, "*.log"))

        # get number of logs
        lnum = len(logs)

        for ln, l in enumerate(logs):
            # get file name from path
            (h, name) = os.path.split(l)
            # generate destination filename
            dest = os.path.join(config[section]["dest"], name)
            progress_update('log-srcdest', lnum, ln, src=name, dest=dest)
            # make sure directory exists
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            # copy log file into new directory
            shutil.copyfile(l, dest)
            # copy metadata
            shutil.copystat(l, dest)

        sync_obj.sync_files(src_dir, config[section]["dest"])

    # do things that are saved till the end
    sync_obj.finish_tasks()

    #return the set of copied files
    return sync_obj.copied_files

def import_sync(src, dest, progress_update=terminal_progress_update, **kwargs):
    #create a sync object
    sync_obj = TestSyncer(progress_update=progress_update, **kwargs)
    # print message
    progress_update('main-srcdest', 0, 0, src=src, dest=dest)
    # call sync function, don't copy data in the revers direction
    sync_obj.sync_files(src, dest)
    # do things that are saved till the end
    sync_obj.finish_tasks()

    #return the set of copied files
    return sync_obj.copied_files

# main function
def main():
    # get path name that this file is in
    file_path = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(
        description="Copy MCV data files between drive and computers"
    )
    parser.add_argument(
        "- i",
        "--import",
        dest="imp",
        action="store",
        default=None,
        metavar="DIR",
        nargs=2,
        help="Use to import data from a given project folder",
    )
    parser.add_argument(
        "--cull",
        dest="cull",
        action="store_true",
        default=False,
        help="Remove old files from source directory",
    )
    parser.add_argument(
        "--no-cull",
        dest="cull",
        action="store_false",
        help="Do not remove old files from source directory",
    )
    parser.add_argument(
        "--sunset",
        dest="sunset",
        type=int,
        default=30,
        help="Delete files older than sunset days",
    )
    parser.add_argument(
        "--superficial",
        dest="thorough",
        action="store_false",
        default=False,
        help="Don't decend into datadir subfolders to check if new files exist",
    )
    parser.add_argument(
        "--thorough",
        dest="thorough",
        action="store_true",
        default=False,
        help="Decend into datadir subfolders to check if new files exist",
    )
    parser.add_argument(
        "-C",
        "--config",
        default=os.path.join(file_path, "testCpy.cfg"),
        metavar="CFG",
        dest="config",
        help="Path to configuration file (defaults to %(default)s)",
    )
    parser.add_argument(
        "--bidirectional",
        action='store_true',
        dest="bd",
        help="sync in both directions",
    )
    parser.add_argument(
        "--one-direction",
        action='store_false',
        dest="bd",
        help="sync only in one direction",
    )

    args = parser.parse_args()

    test_sync_arg_names = ('bd', 'thorough', 'cull', 'sunset')
    #extract arguments for TestSyncer
    test_sync_args = {k:v for k,v in vars(args).items() if k in test_sync_arg_names}

    # check if import argument was given
    if args.imp is None:
        files = export_sync(args.config, **test_sync_args)
        print(f'The following tests were copied : {" ,".join(files)}')
    else:
        # get source and destination folders from argument
        src = args.imp[0]
        dest = args.imp[1]
        # call import sync
        import_sync(src, dest, **test_sync_args)

if __name__ == "__main__":
    main()