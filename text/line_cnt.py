import os

# 递归统计文件夹中所有文本文件行数
def count_lines_in_folder(folder_path):
    total_lines = 0
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 只处理文本文件
            if file.endswith('.java'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding="utf8") as f:
                    lines = f.readlines()
                    total_lines += len(lines)
        for dir in dirs:
            # 递归处理子文件夹
            subdir_path = os.path.join(root, dir)
            total_lines += count_lines_in_folder(subdir_path)
    return total_lines

# 示例用法
folder_path = r'C:\Users\32604\Desktop\work\chalco\chalco-safepm\chalco-safe-JiTuan\safe-jituan\src'
total_lines = count_lines_in_folder(folder_path)
print('Total lines in folder:', total_lines)