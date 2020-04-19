import sys
import os

headline = ['#','##','###','####','#####','######']
lines_in_file = []

"""生成目录列表中的某一项"""
def creat_directory_line(line,headline_mark):
    if headline_mark == '#':
        return '[' + line[2:-1] + '](#' + line[2:-1] + ")\n\n"
    elif headline_mark == '##':
        #&emsp;为Markdown中的一种缩进，这里不直接用空格作为缩进是因为多个空格一起出现可能会生成代码块，引发歧义
        return '&emsp;[' + line[3:-1] + '](#' + line[3:-1] + ")\n\n"
    elif headline_mark == '###':
        return '&emsp;&emsp;[' + line[4:-1] + '](#' + line[4:-1] + ")\n\n"
    elif headline_mark == '####':
        return '&emsp;&emsp;&emsp;[' + line[5:-1] + '](#' + line[5:-1] + ")\n\n"
    elif headline_mark == '#####':
        return '&emsp;&emsp;&emsp;&emsp;[' + line[6:-1] + '](#' + line[6:-1] + ")\n\n"
    elif headline_mark == '######':
        return '&emsp;&emsp;&emsp;&emsp;&emsp;[' + line[7:-1] + '](#' + line[7:-1] + ")\n\n"

"""生成目录列表"""
def creat_directory(f):
    directory = []
    for line in f:
        lines_in_file.append(line)
    f.close()
    for line in lines_in_file:
        splitedline = line.lstrip().split(' ')
        if splitedline[0] in headline:
            directory.append(creat_directory_line(line,splitedline[0]))
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
