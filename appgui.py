import sys
import time
import webbrowser
from tkinter import END, Frame, scrolledtext, StringVar, IntVar, OptionMenu, Toplevel, Checkbutton, BooleanVar
from tkinter.ttk import Button, Entry, Combobox

from reddit import *
from utils import convert65536


# Custom dialog box
class Dialog(Toplevel):

    def __init__(self, parent, url, title=None):
        Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.url = url
        self.result = None
        self.buttonbox()
        self.grab_set()
        self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.geometry("+%d+%d" % (parent.winfo_rootx()+100,
                                  parent.winfo_rooty()+100))
        self.initial_focus.focus_set()
        self.lift()
        self.attributes('-topmost', True)
        self.wait_window(self)

    def buttonbox(self):
        box = Frame(self)
        w = Button(box, text="Open link", width=10, command=self.ok, default="active")
        w.pack(side="left", padx=5, pady=5)
        w = Button(box, text="Close", width=10, command=self.close)
        w.pack(side="left", padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.close)

        box.pack()

    def ok(self, event=None):
        webbrowser.open(self.url)
        self.initial_focus.focus_set()  # put focus back
        self.withdraw()
        self.update_idletasks()

        self.close()

    def close(self, event=None):
        self.parent.focus_set()
        self.destroy()


# Custom scrolled text with highlighting
class CustomText(scrolledtext.ScrolledText):
    def __init__(self, *args, **kwargs):
        scrolledtext.ScrolledText.__init__(self, *args, **kwargs)
        self.configure_tags()

    def configure_tags(self):
        self.tag_configure("error", foreground="#ff0000")
        self.tag_configure("info", foreground="#00ff30")
        self.tag_configure("result", foreground="#0000ff")

    def highlight_pattern(self, pattern, tag, start="1.0", end="end", regexp=False):
        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = IntVar()
        while True:
            index = self.search(pattern, "matchEnd", "searchLimit", count=count, regexp=regexp)
            if index == "":
                break
            if count.get() == 0:
                break
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")

    def highlight(self):
        self.highlight_pattern("Error:", "error")
        self.highlight_pattern("Info:", "info")
        for i in ["Title:", "Url:", "Created:"]:
            self.highlight_pattern(i, "result")

    def tinsert(self, msg):
        self.configure(state="normal")
        self.insert(END, msg)
        self.configure(state="disabled")
        self.highlight()
        self.see(END)


# Center the window
def center(toplevel):
    toplevel.update_idletasks()
    w = toplevel.winfo_screenwidth()
    h = toplevel.winfo_screenheight()
    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = w / 2 - size[0] / 2
    y = h / 2 - size[1] / 2
    toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))


# Main GUI
class Notifier(Frame):
    def __init__(self, parent):
        Frame.__init__(self, parent)
        self.parent = parent
        self.text_clicked = False
        self.time_clicked = False
        self.running = False
        self.initUI()

    def initUI(self):
        # Establish frames
        self.pack(side="top", fill="both", expand=True)

        self.top_frame = Frame(self)
        self.bottom_frame = Frame(self)
        self.top_frame.pack(side="top", fill="both", expand=False)
        self.bottom_frame.pack(side="bottom", fill="both", expand=True)

        self.top_top_frame = Frame(self.top_frame)
        self.top_top_frame.pack(side="top", fill="both", expand=False)
        self.bottom_top_frame = Frame(self.top_frame)
        self.bottom_top_frame.pack(side="bottom", fill="both", expand=False)

        # Entry combo box

        self.cboxv = StringVar(self.top_top_frame)
        self.cbox = Combobox(self.top_top_frame, value=self.cboxv, width=40)
        self.cbox['values'] = ("all", "FreeGamesOnSteam", "funny", "news")
        self.cbox.current(0)
        self.cbox.bind("<Button-1>", self.text_callback)
        self.cbox.bind("<Tab>", self.time_callback)
        self.cbox.pack(side="left", padx=10, pady=10, expand=True)

        # Entry time box
        self.tentry = Entry(self.top_top_frame, width=8, foreground='gray')
        self.tentry.bind("<Button-1>", self.time_callback)
        self.tentry.insert(0, "Time(s)")
        self.tentry.pack(side="left", padx=10, pady=10, expand=True)

        # Category drop-down menu
        self.category = StringVar(self.top_top_frame)
        self.category.set("hot")  # default value

        self.omenu = OptionMenu(self.top_top_frame, self.category, "hot", "new", "top", "controversial", "rising")
        self.omenu.pack(side="right", padx=10, pady=10, expand=True)

        # Limit drop-down menu
        self.limit = IntVar(self.top_top_frame)
        self.limit.set(5)  # default value

        self.lmenu = OptionMenu(self.top_top_frame, self.limit, *list(range(10)))
        self.lmenu.pack(side="right", padx=10, pady=10, expand=True)

        # Scan button
        self.scanb = Button(self.bottom_top_frame, text="Scan", command=self.scan_subreddit)
        self.scanb.pack(side="left", padx=10, pady=10, expand=True)
        self.parent.bind("<Return>", lambda x: self.scan_subreddit())

        # Popup check
        self.checkvar = BooleanVar()
        self.check = Checkbutton(self.bottom_top_frame, text="Popup", variable=self.checkvar)
        self.check.pack(side="left", padx=10, pady=10, expand=True)

        # Continuous check
        self.contvar = BooleanVar()
        self.contb = Checkbutton(self.bottom_top_frame, text="Continuous", variable=self.contvar)
        self.contb.pack(side="left", padx=10, pady=10, expand=True)

        # Stop button
        self.stopb = Button(self.bottom_top_frame, text="Stop", command=self.stop_scanning, state="disabled")
        self.stopb.pack(side="right", padx=10, pady=10, expand=True)
        self.parent.bind("<Escape>", lambda x: self.stop_scanning())

        # Results text box
        self.text = CustomText(self.bottom_frame, height=10, width=50)
        self.text.configure(state="disabled")
        self.text.pack(side="top", padx=10, pady=10, expand=True, fill="both")

    def text_callback(self, event=None):
        if not self.text_clicked:
            self.cbox.delete(0, "end")
            self.text_clicked = True

    def time_callback(self, event=None):
        if not self.time_clicked:
            self.tentry.delete(0, "end")
            self.tentry.config(foreground="black")
            self.time_clicked = True

    def scan_subreddit(self):
        self.running = True
        self.scanb.config(state="disabled")
        self.stopb.config(state="normal")
        self.omenu.config(state="disabled")
        self.lmenu.config(state="disabled")
        self.cbox.config(state="disabled")
        self.tentry.config(state="disabled")
        self.check.config(state="disabled")
        self.contb.config(state="disabled")

        self.parent.unbind("<Return>")
        # Clean text box
        self.text.config(state="normal")
        self.text.delete(1.0, 'end')
        self.text.config(state="disabled")

        # Get values from boxes
        sub_name = self.cbox.get()
        cat = self.category.get()
        self.slimit = self.limit.get()
        self.popup = self.checkvar.get()
        self.cont = self.contvar.get()

        try:
            subreddit = reddit.subreddit(sub_name)
        except Exception:
            self.text.tinsert("Error: insert a subreddit" + '\n')
            self.stop_scanning()
            return

        try:
            self.stime = max(0, int(self.tentry.get()))
        except Exception:
            self.text.tinsert("Error: time must be a number" + '\n')
            self.stop_scanning()
            return

        self.text.tinsert("Info: getting " + cat + " posts from /r/" + sub_name + '\n')

        self.subcat = get_subreddit_cat(subreddit, cat)
        self.get_results()

    def stop_scanning(self):
        self.running = False
        self.scanb.config(state="normal")
        self.stopb.config(state="disabled")
        self.omenu.config(state="normal")
        self.lmenu.config(state="normal")
        self.cbox.config(state="normal")
        self.tentry.config(state="normal")
        self.check.config(state="normal")
        self.contb.config(state="normal")
        self.parent.bind("<Return>", lambda x: self.scan_subreddit())
        self.parent.after_cancel(self.afterv)

    def get_results(self):
        if self.running:
            now = time.time()
            for i in range(5):
                try:
                    submissions = [x for x in self.subcat(limit=self.slimit) if (now - x.created_utc) < self.stime]
                    break
                except Exception:
                    self.text.tinsert("Error: try " + str(i+1) + ", cannot access subreddit" + '\n')
                    if i is 4:
                        self.stop_scanning()
                        return

            nows = time.strftime("%H:%M:%S", time.localtime())

            if not submissions:
                self.text.tinsert("Info: [" + nows + "] no results found" '\n')
            else:
                self.text.tinsert("Info: [" + nows + "] " + str(len(submissions)) + " results found" '\n')

            self.manage_submissions(submissions)
            if self.cont:
                self.text.tinsert("Info: [" + nows + "] continuous mode, will check again in " + str(self.stime) + " seconds\n\n")
                self.afterv = self.parent.after(self.stime*1000, self.get_results)
            else:
                self.text.tinsert("Info: [" + nows + "] scanning finished" '\n')
                self.stop_scanning()

    def manage_submissions(self, sub):
        if sub:
            s = sub[0]
            self.text.tinsert("Title: " + convert65536(s.title) + '\n')
            self.text.tinsert("Url: " + s.url + '\n')
            self.text.tinsert("Created: " + pretty_date(s) + '\n')
            self.parent.update_idletasks()
            if self.popup:
                if sys.platform.startswith('win'):
                    import winsound
                    winsound.PlaySound("media/jamaica.wav", winsound.SND_FILENAME)
                Dialog(self.parent, s.url)
            self.parent.after(750, lambda: self.manage_submissions(sub[1:]))
