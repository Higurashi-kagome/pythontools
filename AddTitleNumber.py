import sys
import os

headline = ['#','##','###','####','#####','######']
title_sign_list = []
"""用于判断标题产生环境"""
insertion = []
"""保存嵌入了编号的标题，用于产生新编号"""

"""给某一行添加编号"""
def add_number_for_line(line_which_is_title,title_sign):
    title_sign_list.append(title_sign)
    if len(title_sign_list) == 1:#如果line_which_is_title是第一个标题
        insertion.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' 1. '))
        return insertion[0]
    else:
        if len(title_sign) == len(title_sign_list[0]):#如果line_which_is_title是一级标题（与第一个标题等级别）
            for insert in insertion[::-1]:#倒序遍历产生了编号的所有标题
                if len(insert.lstrip().split(' ',1)[0]) == len(title_sign):#如果发现等级别的标题
                    insertion.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(insert.lstrip().split(' ',1)[1][0]) + 1) + '. '))
                    return insertion[-1]
        if len(title_sign_list[-2]) == len(title_sign_list[0]):#如果line_which_is_title的上一级标题为一级标题（与第一个标题等级别）
            insertion.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + insertion[-1].lstrip().split(' ')[1] + '1 '))
            return insertion[-1]
        elif len(title_sign_list[-1]) > len(title_sign_list[-2]):#如果line_which_is_title的上一个标题比它更高
            insertion.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + insertion[-1].lstrip().split(' ')[1] + '.1 '))
            return insertion[-1]
        elif len(title_sign_list[-1]) == len(title_sign_list[-2]):#如果line_which_is_title与上一个标题等级别
            insertion.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + insertion[-1].lstrip().split(' ')[1][:-1] +str(int(insertion[-1].lstrip().split(' ')[1][-1]) + 1) + ' '))
            return insertion[-1]
        elif len(title_sign_list[-1]) < len(title_sign_list[-2]):#如果line_which_is_title的上一个标题比它更低
            for insert in insertion[::-1]:#倒序遍历产生了编号的所有标题
                if len(insert.lstrip().split(' ',1)[0]) == len(title_sign):#如果发现等级别的标题
                    insertion.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + insert.lstrip().split(' ')[1][:-1] + str(int(insert.lstrip().split(' ')[1][-1]) + 1) + ' '))
                    return insertion[-1]

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
with open(file_name,'r',encoding='utf-8') as f:
    create_markdown_file_with_number(f)