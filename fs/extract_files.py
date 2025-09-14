import os
import re
import tarfile
import tempfile
import shutil
from pathlib import Path

def find_files(root_dir, pattern):
    """
    在指定目录中递归查找文件名匹配正则表达式的文件
    """
    matched_files = []
    regex = re.compile(pattern)
    
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if regex.search(file):
                full_path = os.path.join(root, file)
                matched_files.append(full_path)
    
    return matched_files

def create_archive(files, root_dir, output_path):
    """
    创建压缩包，保持原始目录结构
    """
    with tarfile.open(output_path, "w:gz") as tar:
        for file_path in files:
            # 计算在压缩包中的相对路径
            arcname = os.path.relpath(file_path, root_dir)
            tar.add(file_path, arcname=arcname)

def main():
    # 提示用户输入搜索路径
    search_path = input("请输入要搜索的目录路径: ").strip()
    
    # 检查搜索路径是否存在
    if not search_path:
        print("错误：路径不能为空")
        return
    
    if not os.path.isdir(search_path):
        print(f"错误：路径 '{search_path}' 不存在或不是目录")
        return
    
    # 提示用户输入正则匹配模式
    pattern = input("请输入文件名的正则匹配模式 (默认: .*java): ").strip()
    if not pattern:
        pattern = '.*java'
    
    print(f"在 '{search_path}' 中搜索匹配模式 '{pattern}' 的文件...")
    
    # 查找文件
    matched_files = find_files(search_path, pattern)
    
    if not matched_files:
        print("未找到匹配的文件")
        return
    
    print(f"找到 {len(matched_files)} 个匹配的文件：")
    for file in matched_files:
        print(f"  {file}")
    
    # 询问是否创建压缩包
    create_archive_choice = input("\n是否创建压缩包？(y/n，默认: y): ").strip().lower()
    if create_archive_choice in ['n', 'no', '否']:
        print("已跳过创建压缩包")
        return
    
    # 创建压缩包
    archive_name = f"extracted_files_{pattern.replace('*', 'all').replace('?', 'any')}.tar.gz"
    archive_path = os.path.join(search_path, archive_name)
    
    # 确保压缩包文件名有效
    archive_path = re.sub(r'[<>:"/\\|?*]', '_', archive_path)
    
    try:
        create_archive(matched_files, search_path, archive_path)
        print(f"\n已创建压缩包：{archive_path}")
    except Exception as e:
        print(f"创建压缩包时出错：{e}")
        return

if __name__ == "__main__":
    main()