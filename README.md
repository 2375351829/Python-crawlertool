# 图片爬虫2 项目结构与功能说明

## 目录结构

```
main.py                # 程序入口，启动UI
ui.py                  # UI界面与交互逻辑（含侧边栏布局）
crawler.py             # 爬虫核心功能（搜索、下载）
preview.py             # 图片预览处理
utils.py               # 工具函数
requirements.txt       # 依赖
README.md              # 结构与功能说明
CHANGELOG.md           # 版本更新说明
```

## 各模块功能说明

### main.py
- 作用：程序入口，初始化 Tkinter，创建 UI 实例，启动主循环。
- 主要内容：
  ```python
  import tkinter as tk
  from ui import ImageCrawlerUI

  if __name__ == '__main__':
      root = tk.Tk()
      app = ImageCrawlerUI(root)
      root.after(100, app.check_queue)
      root.mainloop()
  ```

### ui.py
- 作用：负责所有界面布局、事件绑定、与爬虫/预览模块的交互。
- 主要功能：
  - 侧边栏菜单（如首页、设置、关于等）
  - 主内容区（搜索、预览、下载等）自适应窗口大小
  - 关键词、页码、保存路径、下载序号输入
  - 搜索、下载按钮
  - 预览区（缩略图+序号）
  - 进度显示
  - 多线程处理，防止UI卡死
  - 调用 crawler.py 和 preview.py 的接口
- 主要类与方法：
  - `ImageCrawlerUI`：主UI类
    - `__init__(self, root)`：初始化UI
    - `create_layout(self)`：创建侧边栏+主内容区布局
    - `create_widgets(self, parent)`：主内容区控件
    - `choose_path(self)`：选择保存路径
    - `search_images(self)`：触发搜索
    - `search_thread(self, keyword, page)`：子线程搜索
    - `show_preview(self, preview_data)`：显示缩略图
    - `download_selected_images(self)`：解析下载输入
    - `download_imgs_thread(self, idxs, save_path)`：下载本页图片
    - `download_pages_thread(self, keyword, start_page, end_page, save_path)`：下载多页图片
    - `check_queue(self)`：UI队列处理

### crawler.py
- 作用：实现图片搜索、下载等核心爬虫逻辑。
- 主要函数：
  - `search_images(keyword, page)`
    - 作用：根据关键词和页码，从Bing图片搜索获取图片src列表。
    - 参数：
      - `keyword`：搜索关键词（str）
      - `page`：页码（int，从1开始）
    - 返回：图片src链接列表（list of str）
  - `download_images(srcs, save_path, idxs, queue=None)`
    - 作用：下载指定图片src列表到本地，文件名用序号命名。
    - 参数：
      - `srcs`：图片src链接列表（list of str）
      - `save_path`：保存目录（str）
      - `idxs`：图片序号列表（list of int），用于命名
      - `queue`：可选，进度队列
    - 返回：无
  - `download_pages(keyword, start_page, end_page, save_path, queue=None)`
    - 作用：下载指定关键词和页码范围内的所有图片。
    - 参数：
      - `keyword`：搜索关键词（str）
      - `start_page`：起始页码（int）
      - `end_page`：结束页码（int）
      - `save_path`：保存目录（str）
      - `queue`：可选，进度队列
    - 返回：无

### preview.py
- 作用：负责图片缩略图的下载、处理、Tk对象生成。
- 主要函数：
  - `fetch_thumbnails(img_srcs)`
    - 作用：批量下载图片缩略图并返回(src, PIL.Image对象)元组列表。
    - 参数：
      - `img_srcs`：图片src链接列表（list of str）
    - 返回：`[(src, PIL.Image对象), ...]`

### utils.py
- 作用：通用工具函数
- 主要函数：
  - `parse_seq_input(seq_input, max_idx)`
    - 作用：解析用户输入的图片序号/范围字符串，返回有效序号列表。
    - 参数：
      - `seq_input`：用户输入的序号字符串（str）
      - `max_idx`：当前最大可用序号（int）
    - 返回：有效图片序号列表（list of int）

---

## 功能说明

- 支持 Bing 图片关键词搜索，自动分页
- 支持图片缩略图预览，序号显示
- 支持输入序号/范围/页码下载图片
- 支持多线程，UI不卡死
- 结构清晰，便于扩展（如支持其他图片站、更多过滤条件等）
- 支持侧边栏菜单，主内容区自适应窗口
- 支持自定义背景透明度和毛玻璃（Acrylic）效果
- 下载图片时自动判断和修正文件后缀，确保为图片格式
- 预览区支持无限下拉加载更多图片，滚动到底部自动加载下一页
- 缩略图右键菜单支持“下载此图”和“放大预览”

---

## 后续扩展

- 支持多站点图片爬取
- 支持图片尺寸/大小/类型等更多过滤
- 支持断点续传、失败重试
- 支持下载大图/原图
- 支持批量导出图片信息 
