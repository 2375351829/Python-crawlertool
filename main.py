import tkinter as tk
from ui import ImageCrawlerUI

if __name__ == '__main__':
    root = tk.Tk()
    app = ImageCrawlerUI(root)
    root.after(100, app.check_queue)
    root.mainloop() 