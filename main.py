from tkinter import Tk
from appgui import center, Notifier

def main():
    root = Tk()
    root.wm_title("Subreddit scanner")
    root.geometry("620x370+745+745")
    center(root)
    root.iconbitmap('media/flancito.ico')
    Notifier(root)
    root.mainloop()

if __name__ == '__main__':
    main()
