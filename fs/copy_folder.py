import shutil

def copy_folder(start, to):
	try:
		print('复制', start, to)
		shutil.copytree(start, to)
	except Exception as e:
		return print('移动失败', e)

if __name__ == '__main__':
    # 要移动的文件夹
    folder1 = r"C:\Users\liuhao\Desktop\test1"
    # 将文件夹移动到 C:\Users\liuhao\Desktop\test2 并将其命名为 test2
    folder2 = r"C:\Users\liuhao\Desktop\test2\test2"
    copy_folder(folder1, folder2)