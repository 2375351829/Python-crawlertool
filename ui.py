import ttkbootstrap as tb
from ttkbootstrap.constants import PRIMARY, SECONDARY, LIGHT, INFO, WARNING, SUCCESS, ROUND
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import queue
from crawler import search_images, download_images, download_pages
from preview import fetch_thumbnails
from utils import parse_seq_input
from PIL import ImageTk, Image, ImageDraw
import os
import requests
from io import BytesIO

class ImageCrawlerUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Bing图片爬虫')
        self.queue = queue.Queue()
        self.img_srcs = []
        self.thumbnails = []
        self.save_path = os.getcwd()
        self.style = tb.Style('morph')  # Windows11风格主题
        self.alpha = 1.0  # 默认不透明
        self.acrylic = True  # 默认启用毛玻璃
        self.page_size = 60  # 每次加载图片数量
        self.current_page = 1
        self.all_img_srcs = []  # 所有已加载图片src
        self.loading = False
        self.create_layout()
        self.root.update()
        self.apply_window_effects()

    def apply_window_effects(self):
        # 应用透明度和毛玻璃效果
        try:
            if getattr(self, 'acrylic', True):
                self.root.wm_attributes('-alpha', getattr(self, 'alpha', 1.0))
            else:
                self.root.wm_attributes('-alpha', 1.0)
        except Exception:
            pass

    def create_layout(self):
        self.root.geometry('1000x700')
        self.root.resizable(True, True)
        # 侧边栏
        sidebar = tb.Frame(self.root, width=160, bootstyle=SECONDARY)  # type: ignore
        sidebar.pack(side='left', fill='y')
        tb.Label(sidebar, text='菜单', font=('Segoe UI', 16, 'bold'), bootstyle=SECONDARY).pack(pady=18)  # type: ignore
        tb.Button(sidebar, text='首页', command=self.show_home, bootstyle=PRIMARY).pack(fill='x', padx=18, pady=8)  # type: ignore
        tb.Button(sidebar, text='设置', command=self.show_settings, bootstyle=PRIMARY).pack(fill='x', padx=18, pady=8)  # type: ignore
        tb.Button(sidebar, text='关于', command=self.show_about, bootstyle=PRIMARY).pack(fill='x', padx=18, pady=8)  # type: ignore
        # 主内容区
        self.main_frame = tb.Frame(self.root, bootstyle=LIGHT)  # type: ignore
        self.main_frame.pack(side='left', fill='both', expand=True)
        self.create_widgets(self.main_frame)

    def create_widgets(self, parent):
        # 搜索区
        top = tb.Frame(parent, bootstyle=LIGHT)  # type: ignore
        top.pack(fill='x', pady=12)
        tb.Label(top, text='关键词:', font=('Segoe UI', 12)).pack(side='left')  # type: ignore
        self.keyword_entry = tb.Entry(top, width=18, font=('Segoe UI', 12))  # type: ignore
        self.keyword_entry.pack(side='left', padx=5)
        tb.Label(top, text='页码:', font=('Segoe UI', 12)).pack(side='left')  # type: ignore
        self.page_entry = tb.Entry(top, width=5, font=('Segoe UI', 12))  # type: ignore
        self.page_entry.insert(0, '1')
        self.page_entry.pack(side='left', padx=5)
        tb.Label(top, text='保存路径:', font=('Segoe UI', 12)).pack(side='left')  # type: ignore
        self.path_entry = tb.Entry(top, width=28, font=('Segoe UI', 12))  # type: ignore
        self.path_entry.insert(0, self.save_path)
        self.path_entry.pack(side='left', padx=5)
        tb.Button(top, text='选择', command=self.choose_path, bootstyle=INFO).pack(side='left', padx=2)  # type: ignore
        tb.Button(top, text='搜索', command=self.search_images, bootstyle=SUCCESS).pack(side='left', padx=10)  # type: ignore
        # 下载区
        down = tb.Frame(parent, bootstyle=LIGHT)  # type: ignore
        down.pack(fill='x', pady=6)
        tb.Label(down, text='下载序号(如1,3-5):', font=('Segoe UI', 12)).pack(side='left')  # type: ignore
        self.seq_entry = tb.Entry(down, width=15, font=('Segoe UI', 12))  # type: ignore
        self.seq_entry.pack(side='left', padx=5)
        tb.Button(down, text='下载本页', command=self.download_selected_images, bootstyle=WARNING).pack(side='left', padx=10)  # type: ignore
        tb.Label(down, text='或 下载页码范围:', font=('Segoe UI', 12)).pack(side='left')  # type: ignore
        self.range_entry = tb.Entry(down, width=10, font=('Segoe UI', 12))  # type: ignore
        self.range_entry.pack(side='left', padx=5)
        tb.Button(down, text='下载多页', command=self.download_pages_range, bootstyle=WARNING).pack(side='left', padx=10)  # type: ignore
        # 预览区（Canvas+Frame+滚动条）
        preview_bg = '#f7fafd'
        preview_outer = tb.Frame(parent, bootstyle=LIGHT)  # type: ignore
        preview_outer.pack(fill='both', expand=True, pady=10)
        self.preview_canvas = tk.Canvas(preview_outer, bg=preview_bg, highlightthickness=0)
        self.preview_canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar = tb.Scrollbar(preview_outer, orient='vertical', command=self.preview_canvas.yview, bootstyle=ROUND)  # type: ignore
        self.scrollbar.pack(side='right', fill='y')
        self.preview_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.preview_frame = tb.Frame(self.preview_canvas, bootstyle=LIGHT)  # type: ignore
        self.preview_canvas.create_window((0, 0), window=self.preview_frame, anchor='nw')
        self.preview_frame.bind('<Configure>', lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox('all')))
        # 进度条
        self.progress = tb.Progressbar(parent, orient='horizontal', length=420, mode='determinate', bootstyle=INFO)  # type: ignore
        self.progress.pack(pady=8)
        self.status_label = tb.Label(parent, text='', font=('Segoe UI', 11), bootstyle=LIGHT)  # type: ignore
        self.status_label.pack()
        self.preview_canvas.bind('<Configure>', lambda e: self.on_preview_scroll())
        self.preview_canvas.bind_all('<MouseWheel>', lambda e: self.on_preview_scroll())

    def choose_path(self):
        path = filedialog.askdirectory()
        if path:
            self.save_path = path
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def search_images(self):
        keyword = self.keyword_entry.get().strip()
        page = self.page_entry.get().strip()
        if not keyword or not page.isdigit():
            messagebox.showerror('错误', '请输入有效关键词和页码')
            return
        self.status_label.config(text='正在搜索...')
        t = threading.Thread(target=self.search_thread, args=(keyword, int(page)))
        t.daemon = True
        t.start()

    def search_thread(self, keyword, page):
        try:
            img_srcs = search_images(keyword, page, count=self.page_size)
            self.img_srcs = img_srcs
            self.all_img_srcs = img_srcs.copy()
            self.current_page = page
            self.thumbnails = fetch_thumbnails(img_srcs)
            self.queue.put(('preview', self.thumbnails))
        except Exception as e:
            self.queue.put(('error', str(e)))

    def round_corner(self, pil_img, radius=18):
        # 生成圆角图片
        w, h = pil_img.size
        mask = Image.new('L', (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, w, h), radius, fill=255)
        pil_img.putalpha(mask)
        return pil_img

    def load_more_images(self):
        if self.loading:
            return
        self.loading = True
        def _load():
            next_page = self.current_page + 1
            try:
                img_srcs = search_images(self.keyword_entry.get().strip(), next_page, count=self.page_size)
                if not img_srcs:
                    self.loading = False
                    return
                self.all_img_srcs.extend(img_srcs)
                thumbs = fetch_thumbnails(img_srcs)
                self.thumbnails.extend(thumbs)
                self.current_page = next_page
                self.queue.put(('append_preview', thumbs))
            finally:
                self.loading = False
        threading.Thread(target=_load, daemon=True).start()

    def on_preview_scroll(self, event=None):
        # 检查是否接近底部，自动加载更多
        canvas = self.preview_canvas
        if canvas.yview()[1] > 0.95:
            self.load_more_images()

    def show_preview(self, preview_data, append=False):
        if not append:
            for widget in self.preview_frame.winfo_children():
                widget.destroy()
        if not preview_data:
            tb.Label(self.preview_frame, text='无图片', font=('Segoe UI', 14)).pack()  # type: ignore
            return
        thumb_imgs = []
        start_idx = len(self.preview_frame.winfo_children())//2 + 1 if append else 1
        for idx, (src, img) in enumerate(preview_data, start=start_idx):
            try:
                img = img.convert('RGBA')
                img = self.round_corner(img, radius=18)
                tkimg = ImageTk.PhotoImage(img)
                thumb_imgs.append(tkimg)
                card = tb.Frame(self.preview_frame, width=140, height=160, bootstyle=LIGHT)  # type: ignore
                card.grid(row=(idx-1)//6, column=(idx-1)%6, padx=16, pady=16)
                img_label = tk.Label(card, image=tkimg, bg='#f7fafd', bd=0, highlightthickness=0)
                img_label.image = tkimg  # type: ignore
                img_label.pack(pady=(8,2))
                tb.Label(card, text=f'#{idx}', font=('Segoe UI', 11), bootstyle=SECONDARY).pack()  # type: ignore
                # 鼠标悬停高亮
                def on_enter(e, c=card): c.configure(bootstyle=PRIMARY)  # type: ignore
                def on_leave(e, c=card): c.configure(bootstyle=LIGHT)  # type: ignore
                card.bind('<Enter>', on_enter)
                card.bind('<Leave>', on_leave)
                # 右键菜单
                img_label.bind('<Button-3>', lambda e, i=idx-1: self.show_context_menu(e, i))
            except Exception:
                continue
        self.preview_frame.update_idletasks()
        self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox('all'))

    def show_context_menu(self, event, idx):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label='下载此图', command=lambda: self.download_single_image(idx))
        menu.add_command(label='放大预览', command=lambda: self.show_large_preview(idx))
        menu.tk_popup(event.x_root, event.y_root)

    def download_single_image(self, idx):
        # 下载单张图片
        src = self.all_img_srcs[idx]
        save_path = filedialog.asksaveasfilename(defaultextension='.jpg', filetypes=[('图片文件', '*.jpg;*.png;*.jpeg;*.bmp;*.gif;*.webp')])
        if not save_path:
            return
        try:
            resp = requests.get(src, timeout=10)
            with open(save_path, 'wb') as f:
                f.write(resp.content)
            messagebox.showinfo('下载成功', f'图片已保存到\n{save_path}')
        except Exception as e:
            messagebox.showerror('下载失败', str(e))

    def show_large_preview(self, idx):
        # 放大预览图片
        src = self.all_img_srcs[idx]
        try:
            resp = requests.get(src, timeout=10)
            img = Image.open(BytesIO(resp.content))
            win = tk.Toplevel(self.root)
            win.title('放大预览')
            win.geometry('800x600')
            img.thumbnail((780, 580))
            tkimg = ImageTk.PhotoImage(img)
            lbl = tk.Label(win, image=tkimg)
            lbl.image = tkimg
            lbl.pack(expand=True)
        except Exception as e:
            messagebox.showerror('预览失败', str(e))

    def download_selected_images(self):
        seq_input = self.seq_entry.get().strip()
        if not self.img_srcs:
            messagebox.showerror('错误', '请先搜索图片')
            return
        idxs = parse_seq_input(seq_input, len(self.img_srcs))
        if not idxs:
            messagebox.showerror('错误', '请输入有效序号')
            return
        save_path = self.path_entry.get().strip()
        self.progress['value'] = 0
        self.progress['maximum'] = len(idxs)
        self.status_label.config(text='正在下载...')
        t = threading.Thread(target=self.download_imgs_thread, args=(idxs, save_path))
        t.daemon = True
        t.start()

    def download_imgs_thread(self, idxs, save_path):
        try:
            download_images(self.img_srcs, save_path, idxs, self.queue)
            self.queue.put(('done', '下载完成'))
        except Exception as e:
            self.queue.put(('error', str(e)))

    def download_pages_range(self):
        keyword = self.keyword_entry.get().strip()
        page_range = self.range_entry.get().strip()
        save_path = self.path_entry.get().strip()
        if not keyword or not page_range:
            messagebox.showerror('错误', '请输入关键词和页码范围')
            return
        try:
            if '-' in page_range:
                start, end = map(int, page_range.split('-'))
            else:
                start = end = int(page_range)
        except:
            messagebox.showerror('错误', '页码范围格式错误')
            return
        self.progress['value'] = 0
        self.progress['maximum'] = (end-start+1)*35
        self.status_label.config(text='正在下载多页...')
        t = threading.Thread(target=self.download_pages_thread, args=(keyword, start, end, save_path))
        t.daemon = True
        t.start()

    def download_pages_thread(self, keyword, start_page, end_page, save_path):
        try:
            download_pages(keyword, start_page, end_page, save_path, self.queue)
            self.queue.put(('done', '多页下载完成'))
        except Exception as e:
            self.queue.put(('error', str(e)))

    def check_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                if item[0] == 'preview':
                    self.show_preview(item[1])
                    self.status_label.config(text='预览完成')
                elif item[0] == 'append_preview':
                    self.show_preview(item[1], append=True)
                elif item[0] == 'done':
                    self.status_label.config(text=item[1])
                    self.progress['value'] = self.progress['maximum']
                elif item[0] == 'error':
                    messagebox.showerror('错误', item[1])
                    self.status_label.config(text='出错')
                elif isinstance(item, tuple) and len(item) >= 2 and isinstance(item[0], int):
                    self.progress['value'] = item[0]
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def show_home(self):
        self.status_label.config(text='欢迎使用Bing图片爬虫！')

    def show_settings(self):
        # 设置窗口
        settings_win = tb.Toplevel(self.root)
        settings_win.title('设置')
        settings_win.geometry('320x220')
        settings_win.resizable(False, False)
        tb.Label(settings_win, text='背景透明度 (0.2~1.0):', font=('Segoe UI', 12)).pack(pady=12)  # type: ignore
        alpha_var = tk.DoubleVar(value=self.alpha)
        alpha_slider = tb.Scale(settings_win, from_=0.2, to=1.0, orient='horizontal', length=180, variable=alpha_var, bootstyle=INFO)  # type: ignore
        alpha_slider.pack(pady=4)
        alpha_value_label = tb.Label(settings_win, text=f"{alpha_var.get():.2f}", font=('Segoe UI', 11))  # type: ignore
        alpha_value_label.pack()
        def on_alpha_change(val):
            alpha_value_label.config(text=f"{float(val):.2f}")
        alpha_slider.config(command=on_alpha_change)
        tb.Label(settings_win, text='毛玻璃（Acrylic）效果:', font=('Segoe UI', 12)).pack(pady=8)  # type: ignore
        acrylic_var = tk.BooleanVar(value=self.acrylic)
        acrylic_switch = tb.Checkbutton(settings_win, text='启用', variable=acrylic_var, bootstyle=SUCCESS)  # type: ignore
        acrylic_switch.pack()
        def apply_settings():
            self.alpha = alpha_var.get()
            self.acrylic = acrylic_var.get()
            self.apply_window_effects()
        tb.Button(settings_win, text='应用', command=apply_settings, bootstyle=PRIMARY).pack(pady=16)  # type: ignore

    def show_about(self):
        messagebox.showinfo('关于', 'Bing图片爬虫\n作者: 凌风逐月工作室\n版本: v1.3.0\n日期: 2025-07-03') 