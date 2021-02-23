import sys
import os
import time

headline = ['#','##','###','####','#####','######']
lines_in_file = []

"""生成目录列表中的某一项"""
def creat_directory_line(line,headline_mark,i):
    if headline_mark == '#':
        return '<a href="#' + str(i) + '">' + line[2:-1] + "</a>  \n"
    elif headline_mark == '##':
        #&emsp;为Markdown中的一种缩进，这里不直接用空格作为缩进是因为多个空格一起出现可能会生成代码块，引发歧义
        return '&emsp;<a href="#' + str(i) + '">' + line[3:-1] + "</a>  \n"
    elif headline_mark == '###':
        return '&emsp;&emsp;<a href="#' + str(i) + '">' + line[4:-1] + "</a>  \n"
    elif headline_mark == '####':
        return '&emsp;&emsp;&emsp;<a href="#' + str(i) + '">' + line[5:-1] + "</a>  \n"
    elif headline_mark == '#####':
        return '&emsp;&emsp;&emsp;&emsp;<a href="#' + str(i) + '">' + line[6:-1] + "</a>  \n"
    elif headline_mark == '######':
        return '&emsp;&emsp;&emsp;&emsp;&emsp;<a href="#' + str(i) + '">' + line[7:-1] + "</a>  \n"

"""生成目录列表"""
def creat_directory(f):
    i = 0
    directory = []
    directory.append('<a name="index">**Index**</a>\n')
    for line in f:
        lines_in_file.append(line)
    f.close()
    length = len(lines_in_file)
    for j in range(length):
        splitedline = lines_in_file[j].lstrip().split(' ')
        if splitedline[0] in headline:
            #如果为最后一行且末尾无换行（防最后一个字被去除）
            if j == length - 1 and lines_in_file[j][-1] != '\n':
                directory.append(creat_directory_line(lines_in_file[j] + '\n',splitedline[0],i) + '\n')
                lines_in_file[j] = lines_in_file[j].replace(splitedline[0] + ' ',splitedline[0] + ' ' + '<a name="' + str(i) + '">')[:] + '</a><a style="float:right;text-decoration:none;" href="#index">[Top]</a>' + "\n"
                i = i + 1
            else:
                directory.append(creat_directory_line(lines_in_file[j],splitedline[0],i))
                lines_in_file[j] = lines_in_file[j].replace(splitedline[0] + ' ',splitedline[0] + ' ' + '<a name="' + str(i) + '">')[:-1] + '</a><a style="float:right;text-decoration:none;" href="#index">[Top]</a>' + "\n"
                i = i + 1
    return directory

"""以目录列表为参数生成添加目录的文件"""
def creat_file_with_toc(f):
    directory = creat_directory(f)
    file_with_toc = os.getcwd() + '\\file_with_toc.md'
    if not os.path.exists(file_with_toc):
        with open(file_with_toc, 'w+',encoding='utf-8') as f:
            for directory_line in directory:
                f.write(directory_line)
            for line in lines_in_file:
                f.write(line)
            print('文件已生成')
    else:
        print('文件名重复，请修改文件'+'file_with_toc.md'+'的文件名后重试')

if __name__=='__main__':
    file_name = ''
    #如果未传入文件名
    if len(sys.argv) < 2:
        path = os.getcwd()
        file_and_dir = os.listdir(path)
        md_file = []
        for item in file_and_dir:
            if item.split('.')[-1].lower() in ['md','mdown','markdown'] and os.path.isfile(item):
                md_file.append(item)
        if len(md_file) != 0:
            print('当前目录下的Markdown文件：')
            for file in md_file:
                print(file)
            file_name = input('请输入文件名(含后缀)\n')
        else:
            print('该目录下无Markdown文件，即将退出...')
            time.sleep(2)
            os._exit(0)
    else:
        file_name = sys.argv[1]
    if os.path.exists(file_name) and os.path.isfile(file_name):
        with open(file_name,'r',encoding='utf-8') as f:
            creat_file_with_toc(f)
    else:
        msg = "未找到文件"
        print(msg)
