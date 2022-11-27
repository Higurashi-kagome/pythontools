import os


def removefile(file):
	try:
		os.remove(file)
		print('删除', file)
	except Exception as e:
		return print('文件删除失败', e)

if __name__ == '__main__':
    path = r"C:\Users\liuhao\Desktop\test.txt"
    removefile(path)