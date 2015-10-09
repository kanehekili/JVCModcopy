# Copyright 2009 Andreas Balogh
# See LICENSE for details.

""" GUI for modcopy 

on Python atomic operations see http://effbot.org/zone/thread-synchronization.htm
"""


# system imports

import Tkinter as Tk
import tkFileDialog
import Tix
import logging
import threading
import Queue

# local imports

import libmc
from ConfigParser import ConfigParser

# constants

# globals

LOG = logging.getLogger()

# definitions


class MainDialog(object):
    def __init__(self, parent):
        self.toplevel = parent
        self.hl3_keys = None
        # thread variables
        self.preview_t = None
        self.mods = [ ]
        self._modq = Queue.Queue()
        self._scandir = None
        self.should_abort = None

        # control variables
        self.src_text = Tk.StringVar()
        self.dest_text = Tk.StringVar()
        self.scandir = Tk.StringVar()
        self.overwrite = Tk.IntVar()
        
        # frame 0
        self.fr0 = Tk.Frame(self.toplevel)
        self.bu7 = Tix.Button(self.fr0,
                              text = "Scan",
                              command = self.scan,
                              )
        self.bu8 = Tix.Button(self.fr0,
                              text = "Copy",
                              command = self.copy,
                              )
        self.bu9 = Tix.Button(self.fr0, 
                              text = "Exit",
                              command = self.exit,
                              )
        self.bu9.pack(padx = 5, pady = 5, side = "right")
        self.bu8.pack(padx = 5, pady = 5, side = "right")
        self.bu7.pack(padx = 5, pady = 5, side = "right")

        # frame 1
        self.lf1 = Tk.LabelFrame(self.toplevel, 
                            text = "MOD/MOI Directory (Source)",
                            )
        self.en1 = Tix.Entry(self.lf1, 
                             width = 40,
                             textvariable = self.src_text)
        self.bu1 = Tix.Button(self.lf1,
                             text = "Browse...",
                             command = lambda: self.browse_preview(self.en1),
                             )
        self.bu1.pack(padx = 5, pady = 5, anchor = "sw", side = "right")
        self.en1.pack(padx = 5, pady = 5, fill = "x")

        # frame 2
        self.lf2 = Tk.LabelFrame(self.toplevel, 
                            text = "MPG Directory (Destination)",
                            )
        self.en2 = Tk.Entry(self.lf2, 
                            width = 40,
                            textvariable = self.dest_text)
        self.bu2 = Tk.Button(self.lf2,
                             text = "Browse...",
                             command = lambda: self.browse(self.en2),
                             )
        self.cb2 = Tk.Checkbutton(self.lf2,
                                  text = "Overwrite files with same name",
                                  variable = self.overwrite,
                                  command = lambda: LOG.debug("%s", self.overwrite.get()))
        self.bu2.pack(padx = 5, pady = 5, side = "right", anchor = "n")
        self.en2.pack(padx = 5, pady = 5)
        self.cb2.pack()
        
        # frame 3
        self.lf3 = Tk.LabelFrame(self.toplevel,
                                 padx = 5, 
                                 text = "Preview")
        self.la3 = Tk.Label(self.lf3, 
                            width = 65,
                            anchor = "w",
                            textvariable = self.scandir)
        # manually add a scrollbar to HList
        # see also http://effbot.org/zone/tkinter-scrollbar-patterns.htm
        self.sb3 = Tk.Scrollbar(self.lf3, 
                                relief = Tk.SUNKEN)
        self.hl3 = Tix.HList(self.lf3, 
                             columns = 4, 
                             header = True,
                             yscrollcommand = self.sb3.set)
        self.sb3.config(command = self.hl3.yview)
        self.hl3.header_create(0, text = "File")
        self.hl3.header_create(1, text = "Date")
        self.hl3.header_create(2, text = "Size")
        self.hl3.header_create(3, text = "DAR")

        self.la3.pack(expand = True, fill = "both")
        self.sb3.pack(side = Tk.RIGHT, fill = "y", pady = 5)
        self.hl3.pack(expand = True, fill = "both", pady = 5)

        # pack frames
        self.lf1.pack(padx = 5, pady = 5)
        self.lf2.pack(padx = 5, pady = 5)
        self.lf3.pack(padx = 5, pady = 5, expand = True, fill = "both")
        self.fr0.pack(anchor = "e", side = Tk.BOTTOM)

        self.bu8.config(state = Tk.DISABLED)
      
    def browse_preview(self, widget):
        LOG.debug("MainDialog::browse_preview...")
        self.browse(widget)
        self.entry_settext(self.en2, self.en1.get())
        self.scan()

    def browse(self, widget):
        LOG.debug("MainDialog::browse...")
        # Tix.DirSelectDialog is deprecated, thus use tk_chooseDirectory
        d = tkFileDialog.askdirectory()
        # cannot use control variables as the target entry_field is in widget
        self.entry_settext(widget, d)

    def entry_settext(self, widget, _dir):
        s = widget.get()
        widget.delete(0, len(s))
        widget.insert(0, _dir)

    def copy(self):
        LOG.debug("MainDialog::copy...")
        cd = CopyDialog(self.toplevel, self.mods, 
                        self.dest_text.get(), 
                        self.overwrite.get())
        self.scandir.set(cd.summary)
        
    def exit(self):
        LOG.debug("MainDialog::exit...")
        # allow cleanup in mainloop
        self.toplevel.quit()

    def scan(self):
        LOG.debug("MainDialog::scan...")
        self.bu7.config(state = Tk.DISABLED)
        self.bu8.config(state = Tk.DISABLED)
        self.should_abort = False
        # reset GUI
        self.hl3.delete_all()
        self.hl3_keys = [ ]
        self.mods = [ ]
        self.en1.config(state = Tk.DISABLED)
        self.en2.config(state = Tk.DISABLED)
        # fork thread
        self.preview_t = threading.Thread(target=libmc.find_mods, 
                                          args=( self.src_text.get(), ),
                                          kwargs = { "cb": self } )
        self.preview_t.setDaemon(True)
        self.preview_t.start()
        self.toplevel.after(500, func = self.update)

    def update(self):
        self.scandir.set(str(self._scandir))
        self.update_hlist()
        if self.preview_t.isAlive():
            self.toplevel.after(500, func = self.update)
        else:
            # on_thread_terminated
            LOG.debug("MainDialog::on_scan_terminate...")
            self.scandir.set("%i MOD files." % (len(self.mods), ))
            self.en1.config(state = Tk.NORMAL)
            self.en2.config(state = Tk.NORMAL)
            self.bu7.config(state = Tk.ACTIVE)
            if len(self.mods) > 0:
                self.bu8.config(state = Tk.ACTIVE)
            else:
                self.bu8.config(state = Tk.DISABLED)

    def update_hlist(self):
        while True:
            try:
                mod = self._modq.get_nowait()
            except Queue.Empty:
                return
            self.mods.append(mod)
            # add mod to HList
            root, mod_fn, mpg_fn, md, mod_mtime, mod_size_bytes = mod
            mtime_str = "%s" % mod_mtime.strftime("%Y-%m-%d %H:%M:%S")  
            mod_size_str = "%i MB" % ( mod_size_bytes / 1000000 )
            if md["video_format"] > 0:
                dar = "16:9"
            else:
                dar = "4:3"
            try:
                key = "%i" % (self.hl3_keys.index(root), )
            except ValueError: 
                # add a new directory row
                key = "%i" % (len(self.hl3_keys), )
                self.hl3_keys.append(root)
                self.hl3.add(key, text = root)
                # LOG.debug("new root with (%s, %s)", key, root)
            # add child row
            child_key = self.hl3.add_child(key, text = mod_fn)
            # LOG.debug("child with (%s, %s)", child_key, mod_fn)
            size_style = Tix.DisplayStyle(Tix.TEXT, refwindow = self.hl3, anchor = "e")
            dar_style = Tix.DisplayStyle(Tix.TEXT, refwindow = self.hl3, anchor = "c")
            self.hl3.item_create(child_key, 1, text = mtime_str)
            self.hl3.item_create(child_key, 2, text = mod_size_str, style = size_style)
            self.hl3.item_create(child_key, 3, text = dar, style = dar_style)

    def on_status(self, text):
        # child thread
        self._scandir = text
        
    def on_mod(self, mod):
        # child thread
        self._modq.put(mod)


class CopyDialog:
    # FIXME: destroy window only if thread terminated!
    # TODO: call Tk.bell if user clicks parent window
    def __init__(self, parent, mods, dest_dir, overwrite = None):
        self.toplevel = Tk.Toplevel(parent)
        self.copy_file = None
        self.should_abort = False
        # thread variables
        self.copy_t = None
        self._copy_file = None
        self._copy_progress = 0.0
        # copy summary
        self.summary = ""
        
        # build dialog
        self.build()
        # set position and make modal
        self._set_transient(parent)
        self.toplevel.grab_set()
        # start child thread
        self.start_copy(mods, dest_dir, overwrite)
        # create modal dialog
        self.toplevel.after(500, func = self.update)
        self.toplevel.wait_window(self.toplevel)
    
    def build(self):
        # control variables
        self.copy_file = Tk.StringVar()
        
        # frame 0
        self.fr0 = Tix.Frame(self.toplevel)
        self.bu9 = Tix.Button(self.fr0, 
                              text = "Cancel",
                              command = self.cancel,
                              )
        self.bu9.pack(padx = 5, pady = 5)

        # frame 4
        self.lf4 = Tk.LabelFrame(self.toplevel, 
                                 text = "Copy progress",
                                 )
        self.la4 = Tk.Label(self.lf4,
                            width = 40,
                            anchor = "w",
                            textvariable = self.copy_file
                            )
        self.me4 = Tix.Meter(self.lf4, value = 0.0)
        self.la4.pack(padx = 5, pady = 5)
        self.me4.pack(padx = 5, pady = 5)

        # pack frames
        self.lf4.pack(padx = 5, pady = 5)
        self.fr0.pack(side = "bottom")

    def _set_transient(self, master, relx=0.5, rely=0.3):
        """ from Lib/lib-tk/SimpleDialog.py """
        widget = self.toplevel
        widget.withdraw() # Remain invisible while we figure out the geometry
        widget.transient(master)
        widget.update_idletasks() # Actualize geometry information
        if master.winfo_ismapped():
            m_width = master.winfo_width()
            m_height = master.winfo_height()
            m_x = master.winfo_rootx()
            m_y = master.winfo_rooty()
        else:
            m_width = master.winfo_screenwidth()
            m_height = master.winfo_screenheight()
            m_x = m_y = 0
        w_width = widget.winfo_reqwidth()
        w_height = widget.winfo_reqheight()
        x = m_x + (m_width - w_width) * relx
        y = m_y + (m_height - w_height) * rely
        if x+w_width > master.winfo_screenwidth():
            x = master.winfo_screenwidth() - w_width
        elif x < 0:
            x = 0
        if y+w_height > master.winfo_screenheight():
            y = master.winfo_screenheight() - w_height
        elif y < 0:
            y = 0
        widget.geometry("+%d+%d" % (x, y))
        widget.deiconify() # Become visible at the desired location

    def cancel(self):
        LOG.debug("CopyDialog::cancel...")
        self.should_abort = True
        self.bu9.config(state = Tk.DISABLED)

    def start_copy(self, mods, dest_dir, overwrite):
        LOG.debug("CopyDialog::run...")
        # fork thread
        self.copy_t = threading.Thread(target=libmc.copy, 
                                       args= ( mods, dest_dir ),
                                       kwargs = dict(cb = self, overwrite = overwrite ))
        self.copy_t.setDaemon(True)
        self.copy_t.start()

    def update(self):
        self.me4.config(value = self._copy_progress)
        self.copy_file.set(self._copy_file)
        if self.copy_t.isAlive():
            self.toplevel.after(500, func = self.update)
        else:
            # on_thread_terminated
            self.toplevel.destroy()
    
    def on_copy_progress(self, stats, text):
        # child thread
        self._copy_file = text
        copied, mod_count = stats
        self._copy_progress = float(copied) / float(mod_count)
        return self.should_abort

    def on_copy_complete(self, stats):
        # child thread
        copied, mod_count = stats
        self.summary = "%i of %i files copied." % (copied, mod_count)
        

class Config(object):
    def __init__(self, dialog):
        self.dialog = dialog
        self._cp = ConfigParser()

    def ini_filename(self):
        # "~/.modcopy" on unix
        return "modcopy.ini"
    
    def load(self):
        pass
    
    def save(self):
        pass


def gui(src_dir = None, dest_dir = None, overwrite = False):
    # TODO: load/store values from ini file
    
    # initialise Tk
    root = Tix.Tk()
    root.title('modcopy')
    root.protocol('WM_DELETE_WINDOW', root.quit)

    md = MainDialog(root)
    md.src_text.set(src_dir)
    md.dest_text.set(dest_dir)
    md.overwrite.set(overwrite)

    root.mainloop()
    root.destroy()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s %(levelname).4s %(process)d:%(thread)d %(message)s',
                        datefmt='%H:%M:%S')
    gui("e:\\", "d:\\image", True) 