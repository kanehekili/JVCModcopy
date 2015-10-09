# Copyright 2009 Andreas Balogh
# See LICENSE for details.

""" modcopy library

contains actual code to analyse MOD, copy and manipulate MPG files
"""

# system imports

import logging
import datetime
import mmap
import struct
import os
import shutil

# local imports

# constants

# globals

LOG = logging.getLogger()

# definitions

def find_mods(src_dir, cb = None):
    """ command line interface for modcopy
        
    @param src_dir:  source directory to search for MOD/MOI
    @param dest_dir: destination directory for MPG files 
    """
    assert(os.path.exists(src_dir))
    LOG.info("Search %s for MOD files...", src_dir)
    mods = [ ]
    for root, dirs, files in os.walk(src_dir):
        for mod_fn in files:
            fn, ext = os.path.splitext(mod_fn)
            if cb:
                cb.on_status("Scanning %s/%s..." % (root, mod_fn))
            if ext.upper() != ".MOD":
                continue
            fnbase = os.path.join(root, fn)
            moi_fp = "".join((fnbase, ".MOI"))
            mod_fp = os.path.join(root, mod_fn)
            if os.path.exists(moi_fp):
                md = get_moi_details(moi_fp)
                # NOTE: assume there is only one recording taken within one second
                # MOI timestamps have 1 minute resolution, MOD filetime 1 second
                # use MOD filetime to avoid duplicate filenames
                unix_mod_mtime = os.stat(mod_fp).st_mtime
                mod_mtime = datetime.datetime.fromtimestamp(unix_mod_mtime)
                mod_size_bytes = os.stat(mod_fp).st_size
                mpg_fn = "MOV-%s.MPG" % mod_mtime.strftime("%Y%m%d-%H%M%S")  
                mod = (root, mod_fn, mpg_fn, md, mod_mtime, mod_size_bytes)
                if md["video_format"] > 0:
                    dar = "16:9"
                else:
                    dar = "4:3"
                mods.append(mod)
                LOG.info("Found %-20s [%s] %4s %4i MB", 
                         mod_fn, 
                         mod_mtime.isoformat(" "),
                         dar,
                         mod_size_bytes / 1E+6 )
                if cb:
                    cb.on_mod(mod)
            else:
                LOG.warn("no associated MOI file [%s] for [%s]", moi_fp, mod_fn)
    return mods


def copy(mods, dest_dir, cb = None, overwrite = False):
    # start copying the files
    assert(os.path.exists(dest_dir))
    mod_count = len(mods)    
    copied = 0
    for i, mod in enumerate(mods):
        src_dir, mod_fn, mpg_fn, md, mod_mtime, mod_size_bytes = mod
        mod_fp = os.path.join(src_dir, mod_fn)
        mpg_fp = os.path.join(dest_dir, mpg_fn)
        if cb:
            should_abort = cb.on_copy_progress((i+1, mod_count), 
                                               "%s -> %s" % (mod_fn, mpg_fn))
            if should_abort:
                cb.on_copy_complete((copied, mod_count))
                return (copied, mod_count)
        if os.path.exists(mpg_fp):
            if overwrite:
                LOG.info("Overwriting %s to %s", mod_fn, mpg_fn)
            else:
                LOG.info("Skipping, %s already exists", mpg_fn)
                continue
        else:
            LOG.info("Copying %s to %s", mod_fn, mpg_fn)
        # copy2() also copies mtime, like cp -p 
        shutil.copy2(mod_fp, mpg_fp)
        copied += 1
        # NOTE: default mpg aspect ratio is 4:3
        #       change aspect ratio if source is widescreen 16:9 
        if md["video_format"] > 0:
            LOG.info("Updating Aspect Ratio to 16:9 for [%s]", mpg_fn)
            set_mpg_dar(mpg_fp)
    if cb:
        cb.on_copy_complete((copied, mod_count))
    return (copied, mod_count)

DAR_SQUARE = 0x10
DAR_TV = 0x20
DAR_WIDESCREEN = 0x30
MPG_SEQ_HEADER = "\x00\x00\x01\xb3"

def set_mpg_dar(fn, dar = DAR_WIDESCREEN):
    """ change aspect ratio in all sequence headers in mpg file
    - sequence header starts with 00 00 01 B3
    - aspect ratio is encoded in upper nibble at byte with offset 7
        Value    Aspect Ratio
        0        'forbidden'
        1        1:1 Square Pixels
        2        4:3 Display
        3        16:9 Display
        4        2.21:1 Display
        5-15    'reserved'
    
    @param file: mpg file name
    @see:        http://www.fr-an.de/fragen/v06/01_02_02.htm
    """
    fh = open(fn,"r+b")
    try:
        mpg = mmap.mmap(fh.fileno(), 0)
        i = mpg.find(MPG_SEQ_HEADER, 0)
        while i >= 0:
            b7 = ord(mpg[i + 7])
            nb7 = (b7 & 0x0f) | dar
            mpg[i + 7] = chr(nb7)
            i = mpg.find(MPG_SEQ_HEADER, i + 1)
        mpg.close()
    finally:
        fh.close()
    

def get_moi_details(fn):
    """ get recording details from moi file
        
    @param file:  moi file name
    @return:      dictionary containing data from MOI file
    @see:         http://en.wikipedia.org/wiki/MOI_(file_format)
    """    
    md = { }
    fh = open(fn,"rb")
    try:
        b = fh.read(129)
    finally:
        fh.close()
    if b[0:2] == "V6":
        # WARNING: format length may depend on platform
        fmt = "!2sxxhhbbbbxxi"
        if struct.calcsize(fmt) != 18:
            raise TypeError("invalid struct length; adjust unpack format")
        vals = struct.unpack(fmt, b[0:18])
        version, filesize, year, month, day, hour, minute, duration = vals
        md["version"] = version
        md["filesize"] = filesize
        md["datetime"] = datetime.datetime(year, month, day, hour, minute, 0)
        md["duration"] = duration
    else:
        LOG.warning("unsupported MOI version %s in [%s]" % (b[0:2], fn)) 
    md["video_format"] = ord(b[128]) & 4
    return md

