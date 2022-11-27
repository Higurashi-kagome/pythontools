import shutil

# https://stackoverflow.com/questions/123198/how-to-copy-files
if __name__ == '__main__':
    src = r"C:\Users\liuhao\Desktop\test.txt"
    dst = r"C:\Users\liuhao\Desktop\test\test.txt"
    shutil.copyfile(src, dst)