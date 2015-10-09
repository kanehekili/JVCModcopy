#!/usr/bin/env python

# Select mod files from a directory 
#helper GTK for the tkinter interface. Not in use.

import pygtk
pygtk.require('2.0')

import gtk
import modcopy
import sys

# Check for new pygtk: this is new class in PyGtk 2.4
if gtk.pygtk_version < (2,3,90):
    print "PyGtk 2.3.90 or later required for this example"
    raise SystemExit

def passon(result):
    args = ["modcopy.py","-g",result,"/home/matze/Videos/jvc"]
    modcopy.main(args)    
       

def openFolderChooser(selectedFolder):
    """ open a folder chooser with folder preselected
        @param selectedfolder preselected folder 
        @return folder name (string) 
    """
    dialog = gtk.FileChooserDialog("Select mod file folder",None,
            gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    dialog.set_default_response(gtk.RESPONSE_OK)
    dialog.set_filename(selectedFolder);

##hook for multi files
#dialog.set_select_multiple(True)

    fileFilter = gtk.FileFilter()
    fileFilter.set_name("All files")
    fileFilter.add_pattern("*")
    dialog.add_filter(fileFilter)

    auswahl = dialog.run()
    print "wait for action"
    if auswahl == gtk.RESPONSE_OK:
        dateiname = dialog.get_filename();
    else:
        dateiname = None   
    ##scheints nicht zu schliessen
    closewidget(dialog)
    return dateiname

def closewidget(widget):
    widget.destroy()
    while gtk.events_pending():
        gtk.main_iteration(False) 

def main(argv = None):
    if argv is None:
        argv = sys.argv
        
    folderName = openFolderChooser("/");
    if (folderName == None):
        print "Nix ausgewaehlt"
    else:
        print "auswahl:", folderName       
        passon(folderName)

if __name__ == '__main__':
    sys.exit(main())


  
