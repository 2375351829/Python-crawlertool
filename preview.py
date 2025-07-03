from PIL import Image
import requests
from io import BytesIO

def fetch_thumbnails(img_srcs, size=(120, 120)):
    """
    批量下载图片缩略图并返回(src, PIL.Image对象)元组列表。
    :param img_srcs: 图片src链接列表
    :param size: 缩略图尺寸
    :return: [(src, PIL.Image对象), ...]
    """
    result = []
    for src in img_srcs:
        try:
            resp = requests.get(src, timeout=8)
            img = Image.open(BytesIO(resp.content))
            img.thumbnail(size)
            result.append((src, img))
        except Exception:
            continue
    return result 