import sys
import os

headline = ['#','##','###','####','#####','######']
title_sign_list = []
"""用于判断标题产生环境"""
titles_added_number = []
"""保存嵌入了编号的标题，用于产生新编号"""
is_continue = 'N'


"""给某一行添加编号"""
def add_number_for_line(line_which_is_title,title_sign):
    global is_continue
    title_sign_list.append(title_sign)
    if len(title_sign_list) == 1:#如果line_which_is_title是第一个标题
        titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' 1. '))
        return titles_added_number[0]
    else:
        for title in titles_added_number[::-1]:
            if len(title.lstrip().split(' ')[1]) == 2:#如果发现一级标题
                if len(title_sign) == len(title.lstrip().split(' ')[0]):#如果line_which_is_title是一级标题（与第一个标题级别相同）
                    titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. '))
                    return titles_added_number[-1]
                elif len(title_sign) < len(title.lstrip().split(' ')[0]):#如果line_which_is_title是一级标题（比第一个标题级别更高）
                    if is_continue != 'Y':
                        print('Markdown文件中的：' + title.strip() + "\n似乎不规范\n建议将Markdown文件中的标题分级、规范地写好后再继续")
                        is_continue = input('是否忽略此类警告并继续？（Y/N）')
                    if is_continue.strip() == 'Y':
                        titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. '))
                        return titles_added_number[-1]
                    elif is_continue.strip() == 'N':
                        os._exit(0)
                    else:
                        print('接收到Y/N以外的输入，默认退出')
                        os._exit(0)
                else:
                    break
        if len(titles_added_number[-1].lstrip().split(' ')[1]) == 2:#如果line_which_is_title的上一级标题为一级标题
            titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + titles_added_number[-1].lstrip().split(' ')[1] + '1 '))
            return titles_added_number[-1]
        elif len(title_sign_list[-1]) > len(title_sign_list[-2]):#如果line_which_is_title的上一个标题比它更高
            titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + titles_added_number[-1].lstrip().split(' ')[1] + '.1 '))
            return titles_added_number[-1]
        elif len(title_sign_list[-1]) == len(title_sign_list[-2]):#如果line_which_is_title与上一个标题等级别
            titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + titles_added_number[-1].lstrip().split(' ')[1][:-1] + str(int(titles_added_number[-1].lstrip().split(' ')[1][-1]) + 1) + ' '))
            return titles_added_number[-1]
        elif len(title_sign_list[-1]) < len(title_sign_list[-2]):#如果line_which_is_title的上一个标题比它更低
            for title in titles_added_number[::-1]:
                if len(title.lstrip().split(' ')[1]) == 2:#如果先发现一级标题
                    if is_continue != 'Y':
                        print('Markdown文件中的：' + title.strip() + "\n似乎不规范\n建议将Markdown文件中的标题分级、规范地写好后再继续")
                        is_continue = input('是否忽略此类警告并继续？（Y/N）')
                    if is_continue.strip() == 'Y':
                        titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. '))
                        return titles_added_number[-1]
                    elif is_continue.strip() == 'N':
                        os._exit(0)
                    else:
                        print('接收到Y/N以外的输入，默认退出')
                        os._exit(0)
                if len(title.lstrip().split(' ')[0]) == len(title_sign):#如果找到等级别标题
                    titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + title.lstrip().split(' ')[1][:-1] + str(int(title.lstrip().split(' ')[1][-1]) + 1) + ' '))
                    return titles_added_number[-1]


"""给传入内容添加编号"""
def create_lines_with_number(lines_in_file):
    for i in range(len(lines_in_file)):
        title_sign = lines_in_file[i].lstrip().split(' ')
        if title_sign[0] in headline:
            lines_in_file[i] = add_number_for_line(lines_in_file[i],title_sign[0])
    return lines_in_file


"""生成添加了标题编号的文件"""
def create_markdown_file_with_number(f):
    lines_in_file = []
    lines_in_file_with_number = []
    lines_in_file = f.readlines()
    f.close()
    lines_in_file_with_number = create_lines_with_number(lines_in_file)
    markdown_file_with_number = os.getcwd() + '\\markdown_file_with_number.md'
    if not os.path.exists(markdown_file_with_number):
        with open(markdown_file_with_number, 'w+',encoding='utf-8') as f:
            for line in lines_in_file_with_number:
                f.write(line)
            print('文件已生成')
    else:
        print('文件名重复，请修改文件'+'markdown_file_with_number.md'+'的文件名后重试')


file_name = sys.argv[1]
try:
    with open(file_name,'r',encoding='utf-8') as f:
        create_markdown_file_with_number(f)
except:
    msg = "未找到文件"
    print(msg)