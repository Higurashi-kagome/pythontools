import re
import sys

"""
读取 Markdown 文件，复制其中的图片链接为注释，比如：

![图片名称](图片链接)

转换为：

![图片名称](图片链接)

<!-- !-[图片名称](图片链接) -->
"""
def copy_image_links_to_comments(file_path):
    # 读取 Markdown 文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # 新内容列表
    new_content = []

    # 正则表达式匹配 Markdown 图片链接
    img_pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')

    for line in content:
        # 查找所有图片链接
        matches = img_pattern.findall(line)
        if matches:
            for alt_text, link in matches:
                # 复制图片链接为注释
                comment = f'<!-- !-[{alt_text}]({link}) -->'
                img = f'![{alt_text}]({link})'
                line = line.replace(img, f'![{alt_text}]({link})\n\n{comment}')
                print(img)
        new_content.append(line)

    # 将新内容写入文件
    with open(file_path, 'w', encoding='utf-8') as file:
        file.writelines(new_content)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python copy_images.py <markdown_file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    copy_image_links_to_comments(file_path)
