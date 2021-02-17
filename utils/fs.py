import os

def create_dir(dir_name, path=os.getcwd()):# path is optional, current path by default
    try:
        dir_path = os.path.join(path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        else:# directory already exists
            print('{dir_path} already exists.'.format(dir_path=dir_path))
    except Exception as e:
        print(e)

if __name__ == '__main__':
    create_dir('testdir\\testdir')
    pass