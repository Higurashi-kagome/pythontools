import os
from utils.fs import gci

""" 查找依赖文件 """

# 从tmp_del获取不属于tmp_save文件的依赖的所有文件
def get_del_list(tmp_save = [], tmp_del = []):
    global save_list
    new_tmp_save = []
    new_tmp_del = tmp_del.copy()
    # 遍历tmp_save中的每一个文件s
    for s in tmp_save:
        with open(s, 'r', encoding='utf-8') as f:
            text = f.read()
            # 遍历tmp_del，获取所有文件名
            for d in tmp_del:
                (filepath, filename) = os.path.split(d)
                name = filename.split('.')[-2]
                # 判断每个文件名称是否在文件中出现过
                if name in text and d not in save_list: # 是则将文件放入save、new_tmp_save列表，并从new_tmp_del移除
                    save_list.append(d)
                    new_tmp_save.append(d)
                    new_tmp_del.remove(d)
    if len(new_tmp_save) == 0:
        return new_tmp_del
    else:
        return get_del_list(new_tmp_save, new_tmp_del)

def get_files():
    path = r"C:\Users\liuhao\collect\src\main\java\com\netsdk"
    file_list = gci(path)
    print(len(file_list))
    return file_list

save_list = []

if __name__ == '__main__':
    main_file = r"C:\Users\liuhao\collect\src\main\java\com\netsdk\demo\DhBodyRecognition.java"
    # 入口文件放入tmp_save和save_list
    tmp_save = [main_file]
    save_list.append(main_file)
    tmp_del = get_files()
    tmp_del.remove(main_file)
    del_list = get_del_list(tmp_save, tmp_del)
    print(len(del_list))
    for d in del_list:
        print(d)
        # os.remove(d)
    print(len(del_list))
    print(len(save_list))