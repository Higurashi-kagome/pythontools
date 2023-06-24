import os

# 获取文件夹下的文件集合
def get_all_files(path):
	all_file_list = os.listdir(path)
	all_path = []
	# 遍历该文件夹下的所有目录或者文件
	for file in all_file_list:
		filepath = os.path.join(path,file)
		# 如果是文件夹，递归调用函数
		if os.path.isdir(filepath):
			all_path = all_path +  get_all_files(filepath)
		# 如果不是文件夹，保存文件路径及文件名
		elif os.path.isfile(filepath):
			all_path.append(filepath)
	return all_path

if __name__ == '__main__':
    path = r"."
    files = get_all_files(path)
    for f in files:
        print(f)