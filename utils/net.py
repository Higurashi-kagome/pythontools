import requests
requests.packages.urllib3.disable_warnings()

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