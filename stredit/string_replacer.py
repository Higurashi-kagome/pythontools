import re
import sys

def replace_str(str):
    if len(str) > 0 and pattern.search(str):
        str = pattern.sub(replacement, str)
    return str


if __name__ == "__main__":

    print('输入字符串：  #可输入多行，按 Ctrl+D（Windows 命令行下）或 Ctrl+Z（集成开发环境中）后回车结束输入')
    lines=[]
    while True:
        try:
            lines.append(input())
        except:
            break
    print('字符串输入结束...')

    while True:
        pattern = re.compile(input('输入 pattern：'))
        replacement = input('输入 replacement：')
        str = ''
        for line in lines:
            str += replace_str(line) + '\n'
        break
    print('替换结束')
    print(str[:-1])