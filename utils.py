import re

def parse_seq_input(seq_input, max_idx):
    """
    解析用户输入的图片序号/范围字符串，返回有效序号列表。
    :param seq_input: 用户输入的序号字符串（如 1,3-5,7）
    :param max_idx: 当前最大可用序号
    :return: 有效图片序号列表（list of int）
    """
    result = set()
    parts = re.split(r'[，,\s]+', seq_input.strip())
    for part in parts:
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for i in range(start, end+1):
                    if 1 <= i <= max_idx:
                        result.add(i)
            except:
                continue
        else:
            try:
                i = int(part)
                if 1 <= i <= max_idx:
                    result.add(i)
            except:
                continue
    return sorted(result) 