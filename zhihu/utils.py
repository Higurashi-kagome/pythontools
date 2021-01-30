import os
import requests
requests.packages.urllib3.disable_warnings()

def create_dir(dir_name, path=os.getcwd()):# path is optional, current path by default
    try:
        dir_path = os.path.join(path, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        else:# directory already exists
            print('{dir_path} already exists.'.format(dir_path=dir_path))
    except Exception as e:
        print(e)

def is_connected():
    import requests
    try:
        requests.get("https://www.baidu.com/", timeout=2)
    except:
        return False
    return True

if __name__ == '__main__':
    # create_dir('testdir\\testdir')
    print(is_connected())
    pass