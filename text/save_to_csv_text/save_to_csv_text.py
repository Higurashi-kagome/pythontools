import sys

"""
将文本文件内容转换并保存到 CSV 文件中。

该函数读取一个纯文本文件，解析其内容，并将其转换为 CSV 格式，然后保存到指定的 CSV 文件中。
文本文件的内容格式应为每三个字段一行，字段之间用冒号分隔。第一行被视为标题，后续行分别为项目主体内容。

参数：
csv_path (str): 保存 CSV 文件的路径。
text_path (str): 要读取的纯文本文件路径。

返回：
无

示例：python save_to_csv_text.py csv.txt data.txt
"""
def save_to_csv_text(csv_path, text_path):
    # 读取纯文本文件内容
    with open(text_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 按行分割内容（去除空格）
    lines = content.replace(' ', '').split('\n')
    
    # 获取标题
    title = lines[0].strip()  # 获取第一行内容

    # 准备 CSV 内容

    csv_content = ""

    # 每个项目包含 3 行
    for i in range(1, len(lines), 3):  # 从第二行开始，每 3 行处理一个项目
        if i + 2 < len(lines):  # 确保有足够的行数
            subject_name = lines[i].split('：')[1].strip() if '：' in lines[i] else ''
            completion_unit = lines[i + 1].split('：')[1].strip() if '：' in lines[i + 1] else ''
            group_members = lines[i + 2].split('：')[1].strip() if i + 2 < len(lines) else ''

            # 添加到 CSV 内容
            csv_content += f"{title},{subject_name},{completion_unit},{group_members}\n"

    # 保存到 CSV 文本文件
    with open(csv_path, 'w', encoding='utf-8') as csv_file:
        csv_file.write(csv_content)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法：python script.py <csv_file_path> <text_file_path>")
    else:
        csv_file_path = sys.argv[1]
        text_file_path = sys.argv[2]
        save_to_csv_text(csv_file_path, text_file_path)
