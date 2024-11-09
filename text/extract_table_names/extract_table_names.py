import re

"""
统计 SQL 中的表名
"""
def extract_table_names(input_file, output_file):
    # 定义正则表达式
    pattern = re.compile(r'\b(FROM|JOIN)\s+([a-zA-Z0-9_]+)', re.IGNORECASE)

    # 用于存储唯一表名的集合
    table_names = set()

    # 读取指定文本文件的首行
    with open(input_file, 'r', encoding='utf-8') as file:
        first_line = file.readline()

        # 使用正则表达式查找表名
        matches = pattern.findall(first_line)
        for match in matches:
            table_names.add(match[1])  # match[1] 是表名

    # 将唯一的表名写入输出文件
    with open(output_file, 'w', encoding='utf-8') as file:
        for table_name in sorted(table_names):
            file.write(table_name + '\n')

# 指定输入和输出文件
input_file = 'input.txt'  # 替换为你的输入文件名
output_file = 'output.txt'  # 替换为你的输出文件名

# 调用函数
extract_table_names(input_file, output_file)

print(f"表名已提取并写入到 {output_file}")
