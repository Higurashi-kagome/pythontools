import sys
import os

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
    for j in range(len(lines_in_file)):
        splitedline = lines_in_file[j].lstrip().split(' ')
        if splitedline[0] in headline:
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
    file_name = sys.argv[1]
    with open(file_name,'r',encoding='utf-8') as f:
        creat_file_with_toc(f)
