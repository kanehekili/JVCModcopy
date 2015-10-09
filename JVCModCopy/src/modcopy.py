# Copyright 2009 Andreas Balogh
# See LICENSE for details.

"""
MOD/MOI copy utility

Copies MOD movies from SD(HC) card to local filesystem. MOD files are
converted into MPG files. The widescreen flag is detected in the MOI
file and applied to the MPG file.

If no arguments are given a GUI will start. With arguments the 
source and destination diretories given will be used.

Tested with: 
    Panasonic SDR-S7

"""

# system imports

import sys
import logging
import getopt
import os

# local imports

import libmc
import gui

# constants

__version__ = "2009.3"

# globals

LOG = logging.getLogger()

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s %(levelname).4s %(process)d:%(thread)d %(message)s',
                    datefmt='%H:%M:%S')

# definitions

def main(argv = None):
    if argv is None:
        argv = sys.argv
    # check for parameters: w/o start gui
    LOG.debug("starting [%s]", argv[0]) 
    LOG.info("MWM args1 [%s] 2:%s", argv[0],argv[1]) 
    script_name = os.path.basename(argv[0]) 
    LOG.info("Welcome to modcopy, Version %s, (C) Andreas Balogh, 2009", __version__) 
    try:
        opts, args = getopt.getopt(argv[1:], "hfgp", \
                     ["help", "force", "gui", "preview"])
    except getopt.error, ge:
        LOG.error(ge)
        usage(script_name)
        return 2
    LOG.debug("opts: %s, args: %s", opts, args)
    o_gui = False
    o_preview = False
    o_overwrite = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage(script_name)
            return 0
        elif o in ("-f", "--force"):
            o_overwrite = True
        elif o in ("-p", "--preview"):
            o_preview = True
        elif o in ("-g", "--gui"):
            o_gui = True
    if len(args) == 2:
        src_dir = args[0]
        dest_dir = args[1] 
    elif len(args) == 1 :
        src_dir = args[0]
        dest_dir = args[0] 
        o_preview = True
    elif len(args) == 0 :
        src_dir = dest_dir = os.getcwd()
        o_gui = True
    else:
        usage(script_name)
        return 0
    # check directories for existence
    if src_dir and not os.path.exists(src_dir):
        LOG.error("Source directory not found [%s], aborting", src_dir)
        return 1
    if dest_dir and not os.path.exists(dest_dir):
        LOG.warn("Destination directory not found [%s]", dest_dir)
        if not o_preview:
            LOG.info("Creating destination directory [%s]", dest_dir)
            os.makedirs(dest_dir)
    try:
        if o_gui:
            gui.gui(src_dir, dest_dir, o_overwrite)
        else:
            cli(src_dir, dest_dir, o_preview, o_overwrite)
    except StandardError, e:
        LOG.exception(e)
        return 2
    LOG.info("Done.")
    return 0
     
def usage(script_name):
    print
    print "usage: %s [options] [src_dir [dest_dir]]" % (script_name) 
    print """
  src_dir      source directory to search for MOD/MOI
  dest_dir     destination directory for MPG files
options:
  -h, --help    show this help message and exit
  -f, --force   override files with same name in destination directory
  -g, --gui     force interactive mode 
  -p, --preview preview only, don't copy, don't create non-existent directories
"""


def cli(src_dir, dest_dir, preview_only, overwrite):
    """ command line interface for modcopy
        
    @param src_dir:  source directory to search for MOD/MOI
    @param dest_dir: destination directory for MPG files 
    """
    assert(os.path.exists(src_dir))    
    assert(os.path.exists(dest_dir))    
    mods = libmc.find_mods(src_dir)
    LOG.info("Found %i MOD/MOI files.", len(mods))
    if not preview_only:
        LOG.info("Destination dir is [%s]", dest_dir)
        copied, mod_count = libmc.copy(mods, dest_dir, overwrite = overwrite)
        LOG.info("%i of %i files copied", copied, mod_count)


if __name__ == '__main__':
    sys.exit(main())
