import os
import tarfile
import zipfile
import rarfile

# https://zhuanlan.zhihu.com/p/150523934
def unCompress(src_file, dest_dir):
    file_type = str.lower(os.path.splitext(src_file)[-1])
    with open(src_file, 'rb') as file_reader:
        try:
            if file_type in ['.zip', '.war']:
                # 需要安装 zip 包：pip install zipp
                zip_file = zipfile.ZipFile(file_reader)
                for names in zip_file.namelist():
                    zip_file.extract(names, dest_dir)
                zip_file.close()

            elif file_type == '.rar':
                # 需要安装 rar 包：pip install rarfile
                rar = rarfile.RarFile(file_reader)
                os.chdir(dest_dir)
                rar.extractall()
                rar.close()
            else:
                # file_type == '.tgz' or file_type == '.tar' or file_type == '.gz'
                # Python 自带 tarfile 模块
                tar = tarfile.open(fileobj=file_reader)
                for name in tar.getnames():
                    tar.extract(name, dest_dir)
                tar.close()

        except Exception as ex:
            return False
        return True


if __name__ == '__main__':
    # 解压到的目录
    dest_dir = r"C:\Users\liuhao\Desktop\test"
    # 要解压的压缩包
    src_file = r"C:\Users\liuhao\Desktop\test.war"
    result = unCompress(src_file, dest_dir)