import os

"""
打印指定路径下重名的文件
"""
def search_names(path):
    file_dict = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            if file in file_dict:
                file_dict[file].append(os.path.join(root, file))
            else:
                file_dict[file] = [os.path.join(root, file)]
    for filename, paths in file_dict.items():
        if len(paths) > 1:
            print("文件名：", filename, sep="")
            print("路径：\n", "\n".join(paths), sep="")

# 输入要搜索的路径
path = input("请输入路径：")

# 调用函数搜索文件
search_names(path)