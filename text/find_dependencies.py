import sys
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from utils.fs import gci
import re

""" 查找依赖文件 
大华摄像头的 Java 开发包下有很多的枚举、结构体类，在只需要用到其中的一个功能时，大多数的类可以删除
一个个手动删除太麻烦，所以，我先用 IDEA 的 Optimize Imports 来清除多余的 Import，然后参考 https://stackoverflow.com/questions/33933720/how-to-delete-all-comment-lines-in-idea 删除了所有注释
最后，用该工具删除所有与 main_file 不相关的 .java 文件。
如何工作的：
程序获取 search_path 下的所有文件的文件名，判断文件名是否出现在 main_file 文件中，出现则判断为 main_file 要用到，不能删
接着，对找到的不能删的文件递归执行上述过程，找到这些不能删的文件所要用到的文件
最后，将所有没有被判断为不能删的文件删除
"""

main_file = r"C:\Users\liuhao\OneDrive\work\01\src\main\java\com\netsdk\demo\DhBodyRecognition.java"
search_path = r"C:\Users\liuhao\OneDrive\work\01\src\main\java\com\netsdk"

# 从 tmp_del 获取不属于 tmp_save 文件的依赖的所有文件
def get_del_list(tmp_save = [], tmp_del = []):
    global save_list
    new_tmp_save = []
    new_tmp_del = tmp_del.copy()
    # 遍历 tmp_save 中的每一个文件 s
    for s in tmp_save:
        with open(s, 'r', encoding='utf-8') as f:
            text = f.read()
            # 遍历 tmp_del，获取所有文件名
            for d in tmp_del:
                (filepath, filename) = os.path.split(d)
                name = filename.split('.')[-2]
                # 判断每个文件名称是否在文件中出现过
                if re.search(r'(?<![_\w])' + re.escape(name) + r'(?![_\w\d])', text) and d not in save_list: # 是则将文件放入 save、new_tmp_save 列表，并从 new_tmp_del 移除
                    save_list.append(d)
                    new_tmp_save.append(d)
                    new_tmp_del.remove(d)
    if len(new_tmp_save) == 0:
        return new_tmp_del
    else:
        return get_del_list(new_tmp_save, new_tmp_del)

def get_files():
    global search_path
    file_list = gci(search_path)
    print(len(file_list))
    return file_list

save_list = []

if __name__ == '__main__':
    # 入口文件放入 tmp_save 和 save_list
    tmp_save = [main_file]
    save_list.append(main_file)
    tmp_del = get_files()
    if main_file in tmp_del:
        tmp_del.remove(main_file)
    del_list = get_del_list(tmp_save, tmp_del)
    print(len(del_list))
    for d in del_list:
        print(d)
        # os.remove(d)
    print(len(del_list))
    print(len(save_list))