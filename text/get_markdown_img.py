import os
import re
import uuid
import requests

"""
下载 Markdown 文件中的图片，保存到 ./res/<Markdown 文件名> 路径下，
并替换 Markdown 文件中的在线图片链接为本地图片链接
"""
def download_images(md_file):
    # 创建目录
    dir_name = os.path.join("res", os.path.splitext(md_file)[0])
    os.makedirs(dir_name, exist_ok=True)

    # 读取 Markdown 文件
    with open(md_file, "r", encoding="utf-8") as f:
        md_content = f.read()

    # 匹配图片链接
    pattern = r"!\[.*?\]\((https?://.*)\)"
    image_urls = re.findall(pattern, md_content)
    # 下载图片并替换链接
    print('找到' + str(len(image_urls)) + '张图片')
    for url in image_urls:
        response = requests.get(url)
        if response.status_code == 200:
            # 获取文件名
            filename = os.path.basename(url)
            if not filename:
                filename = str(uuid.uuid4()) + ".jpg"
            # 保存图片到本地
            with open(os.path.join(dir_name, filename), "wb") as f:
                f.write(response.content)
            # 替换 Markdown 文件中的链接
            md_content = md_content.replace(url, f"./{dir_name}/{filename}")
        else:
            print("下载图片失败：" + url)
    # 保存更新后的 Markdown 文件
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("下载完成！")

download_images(input("请输入文件路径："))