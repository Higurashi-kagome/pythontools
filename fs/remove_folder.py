import shutil

def remove_folder(folder):
	shutil.rmtree(folder, ignore_errors=True)
	print('删除', folder)

if __name__ == "__main__":
    # 要删除的文件夹
    dest_dir = r"C:\Users\liuhao\Desktop\test"
    remove_folder(dest_dir)