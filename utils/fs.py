import os
import sys

# 在 [path] 路径下创建 <dir_name> 文件夹
# 返回文件夹绝对路径
def create_dir(dir_name, path=sys.path[0]):
    try:
        dir_path = os.path.join(path, dir_name)
        # 路径不存在(存在同名文件时不会尝试创建，否则报错 "[WinError 183]")
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        else:# directory already exists
            print('{dir_path} already exists.'.format(dir_path=dir_path))
    except Exception as e:
        print(e)
    return dir_path

# 在 [path] 路径下创建 <file_name> 文件
# 返回文件绝对路径
def create_file(file_name, path=sys.path[0]):
    try:
        file_path = os.path.join(path, file_name)
        # 路径不存在(存在同名文件夹时不会尝试创建，因为 open 函数在尝试打开文件夹时
        # 报错 "[Errno 13] Permission denied")
        if not os.path.exists(file_path):
            f = open(file_path, "w")
            f.close()
        else:# directory already exists
            print('{file_path} already exists.'.format(file_path=file_path))
    except Exception as e:
        print(e)
    return file_path

if __name__ == '__main__':
    print(create_file("test1"))
    print(create_dir("test2"))
    pass