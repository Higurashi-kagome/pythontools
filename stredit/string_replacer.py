import re

def replace_str(str):
    while True:
        pattern = re.compile(input('输入 pattern：'))
        replacement = input('输入 replacement：')
        if len(str) > 0 and pattern.search(str):
            str = pattern.sub(replacement, str)
            print('替换结束')
        else:
            print('无替换')
        if(input('回车继续，输入任意字符结束：')):
            break
    print(str)


if __name__ == "__main__":
    str = input('输入字符串：')
    replace_str(str)