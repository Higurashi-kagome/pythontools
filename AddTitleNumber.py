import sys
import os

headline = ['#','##','###','####','#####','######']
title_sign_list = []
"""用于判断标题产生环境"""
titles_added_number = []
"""保存嵌入了编号的标题，用于产生新编号"""

"""给特殊行（级别高于第一行标题的行后方的行）添加编号"""
def add_number_specially(line_which_is_title,min_title_sign,title,title_sign):
    if len(title_sign) <= len(min_title_sign):#如果line_which_is_title级别更高或与最高级标题级别相同（#号更少或相同）
        return line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. ')
    else:
        if len(titles_added_number[-1].lstrip().split(' ')[1]) == 2:#如果line_which_is_title的上一级标题为一级标题
            return line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + titles_added_number[-1].lstrip().split(' ')[1] + '1 ')
        elif len(title_sign_list[-1]) > len(title_sign_list[-2]):#如果line_which_is_title的上一个标题比它更高
            return line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + titles_added_number[-1].lstrip().split(' ')[1] + '.1 ')
        elif len(title_sign_list[-1]) == len(title_sign_list[-2]):#如果line_which_is_title与上一个标题等级别
            return line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + titles_added_number[-1].lstrip().split(' ')[1][:-1] +str(int(titles_added_number[-1].lstrip().split(' ')[1][-1]) + 1) + ' ')
        elif len(title_sign_list[-1]) < len(title_sign_list[-2]):#如果line_which_is_title的上一个标题比它更低
           for title in titles_added_number[::-1]:
                if len(title.lstrip().split(' ')[0]) == len(title_sign):#如果找到等级别标题
                    return line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + title.lstrip().split(' ')[1][:-1] + str(int(title.lstrip().split(' ')[1][-1]) + 1) + ' ')
           for title in titles_added_number[::-1]: #没找到等级别标题的时候视为一级标题
                if len(title.lstrip().split(' ')[1]) == 2:#如果找到一级标题（序号长度为2）
                    return line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. ')


"""给某一行添加编号"""
def add_number_for_line(line_which_is_title,title_sign):
    title_sign_list.append(title_sign)
    if len(title_sign_list) == 1:#如果line_which_is_title是第一个标题
        titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' 1. '))
        return titles_added_number[0]
    else:
        for title in titles_added_number[::-1]:#倒序遍历产生了编号的所有标题
            if len(title.lstrip().split(' ',1)[0]) < len(title_sign_list[0]):#如果发现比第一个标题级别更高的标题（#更少的标题）
                titles_added_number.append(add_number_specially(line_which_is_title,min(title_sign[:]),title,title_sign))
                return titles_added_number[-1]
        if len(title_sign) <= len(title_sign_list[0]):#如果line_which_is_title是一级标题
            for title in titles_added_number[::-1]:#倒序遍历产生了编号的所有标题
                if len(title.lstrip().split(' ',1)[0]) <= len(title_sign_list[0]):#如果发现一级标题
                    titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. '))
                    return titles_added_number[-1]
        elif len(titles_added_number[-1].lstrip().split(' ')[1]) == 2:#如果line_which_is_title的上一级标题为一级标题
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
                if len(title.lstrip().split(' ')[0]) == len(title_sign):#如果找到等级别标题
                    titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + title.lstrip().split(' ')[1][:-1] + str(int(title.lstrip().split(' ')[1][-1]) + 1) + ' '))
                    return titles_added_number[-1]
            for title in titles_added_number[::-1]: #没找到等级别标题的时候视为一级标题
                if len(title.lstrip().split(' ')[1]) == 2:#如果找到一级标题（序号长度为2）
                    titles_added_number.append(line_which_is_title.replace(title_sign + ' ',title_sign + ' ' + str(int(title.lstrip().split(' ',1)[1][0]) + 1) + '. '))
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
with open(file_name,'r',encoding='utf-8') as f:
    create_markdown_file_with_number(f)