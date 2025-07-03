import requests
import os
import re
from lxml import html
from PIL import Image
from io import BytesIO

BING_URL = 'https://cn.bing.com/images/async'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

IMG_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}

def search_images(keyword, page=1, count=35):
    """
    根据关键词和页码，从Bing图片搜索获取图片src列表。
    :param keyword: 搜索关键词
    :param page: 页码（从1开始）
    :param count: 每页图片数量
    :return: 图片src链接列表
    """
    first = 1 + (page - 1) * count
    params = {
        'q': keyword,
        'first': first,
        'count': count,
        'cw': 1177,
        'ch': 355,
        'relp': 35,
        'datsrc': 'I',
        'layout': 'RowBased',
        'apc': 0,
        'imgbf': 'DfCtqwgAAACQAQAAAAAAAAAAAAAFAAAAYqYAOeNfTNkKeUBlAgRXXJWokKlUAREAESAoCGuAQGwAxIhQIWqoI4KoEC4sFQ97CSM5uSWcQoDaDgAAAAAAAA%3d%3d',
        'mmasync': 1,
        'dgState': f'x*203_y*1216_h*195_c*1_i*{first}_r*7',
        'IG': '3428107B49654C059711C66D1D0262CC',
        'SFX': page,
        'iid': f'images.{5000+page}',
    }
    resp = requests.get(BING_URL, params=params, headers=HEADERS, timeout=10)
    tree = html.fromstring(resp.text)
    img_srcs = tree.xpath('//img[@class="mimg" or @data-src]/@src | //img[@class="mimg" or @data-src]/@data-src')
    # 去重并过滤空
    img_srcs = [src for src in set(img_srcs) if src and src.startswith('http')]
    return img_srcs

def download_images(srcs, save_path, idxs, queue=None):
    """
    下载指定图片src列表到本地，文件名用序号命名。
    :param srcs: 图片src链接列表
    :param save_path: 保存目录
    :param idxs: 图片序号列表
    :param queue: 可选，进度队列
    """
    os.makedirs(save_path, exist_ok=True)
    for i, idx in enumerate(idxs):
        if idx-1 >= len(srcs):
            continue
        url = srcs[idx-1]
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            # -------- 文件后缀判断与修正 START --------
            # 1. 先从url中提取后缀
            ext = re.findall(r'\.([a-zA-Z0-9]+)(?:\?|$)', url)
            ext = ext[0].lower() if ext else ''
            # 2. 如果不是常见图片格式，则用PIL自动识别图片格式
            if ext not in IMG_EXTS:
                try:
                    img = Image.open(BytesIO(resp.content))
                    if img.format:
                        ext = img.format.lower()  # PIL返回格式如'jpeg', 'png', 'webp'等
                        if ext == 'jpeg':
                            ext = 'jpg'
                        if ext not in IMG_EXTS:
                            ext = 'jpg'  # 兜底
                    else:
                        ext = 'jpg'
                except Exception:
                    ext = 'jpg'  # 识别失败兜底
            # 3. 用修正后的后缀命名文件，确保为图片格式
            # -------- 文件后缀判断与修正 END --------
            fname = os.path.join(save_path, f'{idx}.{ext}')
            with open(fname, 'wb') as f:
                f.write(resp.content)
            if queue:
                queue.put((i+1, len(idxs)))
        except Exception as e:
            if queue:
                queue.put((i+1, len(idxs), str(e)))
            continue

def download_pages(keyword, start_page, end_page, save_path, queue=None):
    """
    下载指定关键词和页码范围内的所有图片。
    :param keyword: 搜索关键词
    :param start_page: 起始页码
    :param end_page: 结束页码
    :param save_path: 保存目录
    :param queue: 可选，进度队列
    """
    idx = 1
    for page in range(start_page, end_page+1):
        srcs = search_images(keyword, page)
        idxs = list(range(1, len(srcs)+1))
        download_images(srcs, save_path, idxs, queue)
        idx += len(srcs) 