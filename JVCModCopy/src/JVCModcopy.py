#!/usr/bin/python
'''
Created on Oct 24, 2014
GTK3 Gui for libmc.py
@author: Kanehekili 
'''

import libmc
import threading
import Queue
from ConfigParser import ConfigParser
import os
from os.path import expanduser

from gi.repository import Gtk,GObject

class MainWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="JVC Mod Importer")
        self.modder = ModCopy() 
        self.isWorkerBusy = False
        self.should_abort=False
        self.config=ConfigAccessor("modcopy.ini")
        self._initWidgets()

    def _initWidgets(self):
        '''
        '''
        self._assureConfig()
        here = os.path.dirname(os.path.realpath(__file__))
        self.set_icon_from_file(os.path.join(here,"jvc.png"))
        mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=4)
        srcBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        destBox= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lowerBtnBox= Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        
        srclabel= Gtk.Label("Source", xalign=0)
        self.srcEdit =Gtk.Entry()
        self.srcEdit.set_editable(False)
        srcButton = Gtk.Button(image=Gtk.Image(stock=Gtk.STOCK_OPEN))
        srcButton.set_tooltip_text("Select the folder of the camera")
        
        srcButton.connect("clicked", self.on_setSource_clicked)
        #expand=false: position stays, 
        srcBox.pack_start(srclabel, False, False, 6)
        srcBox.pack_start(self.srcEdit, True, True, 6)
        srcBox.pack_start(srcButton, False, True, 6)

        destlabel= Gtk.Label("Target", xalign=0)
        self.destEdit =Gtk.Entry()
        self.destEdit.set_editable(False)
        destButton = Gtk.Button(image=Gtk.Image(stock=Gtk.STOCK_OPEN))
        destButton.set_tooltip_text("Select the folder where the file are stored")
        destButton.connect("clicked", self.on_setTarget_clicked)
        destBox.pack_start(destlabel, False, True, 6)
        #expand=true,fill=false, size remains...
        destBox.pack_start(self.destEdit, True, True, 6)
        destBox.pack_start(destButton, False, False, 6)

        myList = self._makeList()
        
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_show_text(True)
        
        
        self.buttonStart = Gtk.Button(label="Start",image=Gtk.Image(stock=Gtk.STOCK_APPLY))
        self.buttonStart.connect("clicked", self.on_start_clicked)
        lowerBtnBox.pack_end(self.buttonStart, False, False, 15)
        
        self.buttonCanx = Gtk.Button(label="Cancel",image=Gtk.Image(stock=Gtk.STOCK_CANCEL))
        self.buttonCanx.connect("clicked", self.on_cancel_clicked)
        lowerBtnBox.pack_end(self.buttonCanx, False, False,0)
        
        self.setButtonActivity(False)
        
        # expand = false, fill not relevant- height stays!
        mainbox.pack_start(srcBox,False,True,0)
        mainbox.pack_start(destBox,False,True,3)
        mainbox.pack_start(myList,True,True,3)
        mainbox.pack_start(self.progressbar,False,True,3)
        mainbox.pack_end(lowerBtnBox,False,False,3)
        
        self.add(mainbox)
        self.set_border_width(5)
        self.set_default_size(self.config.getInt("SCREENX"), self.config.getInt("SCREENY"))
        self.connect("delete-event", self.on_winClose, None)
    
    def _assureConfig(self):

        self.config.read()
        x = self.config.getInt("SCREENX")
        if not x:
            home = expanduser("~")
            self.config.add("SCREENX","400")
            self.config.add("SCREENY","400")
            self.config.add("SRC",home)
            self.config.add("DEST",os.path.join(home,"Videos"))
        
    def _makeList(self):
        self.fileStore = Gtk.ListStore(str,str,str,str);
        theList = Gtk.TreeView(self.fileStore)
        nameRenderer = Gtk.CellRendererText()
        lenRenderer = Gtk.CellRendererText()
        darRenderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("File", nameRenderer, text=0)
        theList.append_column(column)

        column = Gtk.TreeViewColumn("Date", nameRenderer, text=1)
        theList.append_column(column)

        column = Gtk.TreeViewColumn("Size", lenRenderer, text=2)
        theList.append_column(column)
        
        column = Gtk.TreeViewColumn("DAR", darRenderer, text=3)
        theList.append_column(column)
        
        
        swH = Gtk.ScrolledWindow()
        swH.add(theList)
        
        return swH
        
    
    def setButtonActivity(self,isEnabled):
        self.buttonStart.set_sensitive(isEnabled)
        self.buttonCanx.set_sensitive(isEnabled)
    
    def setProgress(self,part,ofAll):
        fraction = part/ofAll
        self.progressbar.set_fraction(fraction)
        
    
    def on_setTarget_clicked(self,widget):
        result = self._selectFolder(self.config.get("DEST"))
        if result:
            self.destEdit.set_text(result)
            self.modder.setTarget(result)
            self.setButtonActivity(True)

    def __cbProgressPulse(self):
        self.progressbar.pulse()
        if not self.isWorkerBusy:
            self.progressbar.set_fraction(0)    
        return self.isWorkerBusy

        
    def on_setSource_clicked(self,widget):
        result = self._selectFolder(self.config.get("SRC"))  
        if result:
            #GObject.timeout_add(250, self.__cbProgressPulse)
            GObject.idle_add(self.__cbProgressPulse)
            self.srcEdit.set_text(result)
        w = Worker(self._fillList,result,self)
        w.start()       

        
    def _fillList(self,result):
        #TODO "reading files...."
        self.fileStore.clear()
        self.modder.setSource(result)
        modList = self.modder.getFiles()
        for item in modList:
            self.fileStore.append(item)

    def _selectFolder(self,defaultFolder):
        dialog = Gtk.FileChooserDialog("Please choose a file", self,Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        dialog.set_filename(defaultFolder)

        self.add_filters(dialog)

        response = dialog.run()
        thePath = None
        if response == Gtk.ResponseType.OK:
            thePath = dialog.get_filename()

        dialog.destroy()
        return thePath
    
        
    def on_start_clicked(self, widget):
        self.should_abort=False
        self.buttonStart.set_sensitive(False)
        self.modder.start_copy(self)
        
    def on_copy_progress(self, stats, text):
        # child thread, called by libmc
        self._copy_file = text
        copied, mod_count = stats
        copy_progress = float(copied) / float(mod_count)
        summary = "%i of %i files copied." % (copied, mod_count)
#        print "copy progess",text," copied:",copied," of:" ,mod_count
        GObject.idle_add(self._asyncSetProgress,summary,copy_progress);
        return self.should_abort

    def _asyncSetProgress(self,summary,copyProgress):
        self.progressbar.set_text(summary)
        self.progressbar.set_fraction(copyProgress)
        

    def on_copy_complete(self, stats):
        # child thread, called by libmc
        copied, mod_count = stats
        summary = "%i of %i files copied to %s" % (copied, mod_count,self.modder.target)
        GObject.idle_add(self._asyncSetProgress,"",0.0);
        GObject.idle_add(self.setButtonActivity,True)
        #GObject.timeout_add(5, self.__cbShowMessage,"Transfer completed", summary)
        GObject.idle_add(self.__cbShowMessage,"Transfer completed", summary)

    def add_filters(self,dialog):
        fileFilter = Gtk.FileFilter()
        fileFilter.set_name("All files")
        fileFilter.add_pattern("*")
        dialog.add_filter(fileFilter)


    def on_cancel_clicked(self, widget):
        if not self.isWorkerBusy:
            return #ignore it
        self.should_abort=True
        self.buttonCanx.set_sensitive(False)
        
    def __cbShowMessage(self,title,text):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, title)
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()   
        return False     

    #Exit the window
    def on_winClose(self, widget, event, data):
        geo = self.get_allocation()
        self.config.add("SCREENX",str(geo.width))
        self.config.add("SCREENY",str(geo.height))
        aPath = self.modder.source
        if self.__verifyPath(aPath):
            self.config.add("SRC",aPath);
        aPath = self.modder.target
        if self.__verifyPath(aPath):            
            self.config.add("DEST",aPath);
        self.config.store()

    def __verifyPath(self,aPath):
        if aPath and len(aPath)>4:
            return os.path.exists(aPath)
        return False


class ModCopy():
    def __init__(self):
        self.source = None
        self.target = None
        self.mods = [ ]
        self._modq = Queue.Queue()
        
    def setSource(self,sourcePath):
        self.source = sourcePath;
        if sourcePath:
            self.scan()
            
    def setTarget(self,targetPath):
        self.target = targetPath;
            
    def _data_Present(self):
        return (self.source is not None) and (self.target is not None)        

    def getFiles(self):
        result=[]
        for modinfo in self.mods:
            root, mod_fn, mpg_fn, md, mod_mtime, mod_size_bytes = modinfo
            timeString = "%s" % mod_mtime.strftime("%Y-%m-%d %H:%M:%S")  
            modSizeMB = "%i MB" % ( mod_size_bytes / 1000000 )
            if md["video_format"] > 0:
                dar = "16:9"
            else:
                dar = "4:3"
            rowData=[mpg_fn,timeString,modSizeMB,dar]
            result.append(rowData)
        if len(result)==0:
            result =[["No files found","-","0","?"]]
        return result
    
    def scan(self):
        #the easy way:
        self.mods = libmc.find_mods(self.source)


    def start_copy(self,gui):
        # fork thread
        self.copy_t = threading.Thread(target=libmc.copy, 
                                       args= ( self.mods, self.target ),
                                       kwargs = dict(cb = gui, overwrite = True ))
        self.copy_t.setDaemon(True)
        self.copy_t.start()


     

#Runs a function in NON gui thread. Informs the client when done.
#the client needs to have the var "isWorkerBusy"
class Worker(threading.Thread):
    def __init__ (self, function, args, parent):
        threading.Thread.__init__(self)
        self.function = function
        self.parent = parent
        self.args = args
 
    def run(self): # when does "run" get executed?
        self.parent.isWorkerBusy = True
        self.function(self.args)
        self.parent.isWorkerBusy = False
 
    def stop(self):
        self = None
    

class ConfigAccessor():
    __SECTION="JVCMODCOPY"
    

    def __init__(self,filePath):
        self._path=filePath
        self.parser = ConfigParser()
        self.parser.add_section(self.__SECTION)

    def read(self):
        self.parser.read(self._path)

    def add(self,key,value):
        self.parser.set(self.__SECTION,key,value)

    def get(self,key):
        if self.parser.has_option(self.__SECTION, key):
            return self.parser.get(self.__SECTION,key)
        return None

    def getInt(self,key):
        if self.parser.has_option(self.__SECTION, key):
            return self.parser.getint(self.__SECTION,key)
        return None

    def store(self):
        try:
            with open(self._path, 'w') as aFile:
                self.parser.write(aFile)
        except IOError:
            return False
        return True


win = MainWindow()
win.connect("delete-event", Gtk.main_quit)
win.show_all()


if __name__ == '__main__':
    GObject.threads_init()
    Gtk.main()