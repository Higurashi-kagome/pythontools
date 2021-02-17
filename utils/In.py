def input_lines():
    print('输入字符串：  #可输入多行，按 Ctrl+Z（Windows 命令行下）或 Ctrl+D（集成开发环境中）后回车结束输入')
    lines=[]
    while True:
        try:
            lines.append(input())
        except:
            break
    print('字符串输入结束...')
    return lines

if __name__ == '__main__':
    print(input_lines())