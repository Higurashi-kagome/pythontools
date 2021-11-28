import sys
sys.path.append('../..')
import requests.packages.urllib3
import traceback
import os
import xlwings as xw
import re
from bs4 import BeautifulSoup
import requests
import time
from utils import fs
requests.packages.urllib3.disable_warnings()

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Host": "ggzy.hengyang.gov.cn",
    "Referer": "https://ggzy.hengyang.gov.cn/jyxx/jsgcjy/zbgg/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
}

# 设置为全局变量，方便错误处理
app = None
wb = None
sheet1 = None
dir_path = None
xlsx_table_head = ['序号', '所属地区', '公告名称', '项目名称', '投资额（万元）', '标段、类型',
        '单位资质要求', '业绩要求', '项目负责人要求','技术负责人要求', '是否联合体',
        '保证金', '获取时间、方式', '开标时间', '业主信息', '代理信息', '本地网页链接', '网页链接', '发布时间']
nrows = 0
ncols = len(xlsx_table_head)

# 正则替换。匹配文字并修改样式
# https://blog.csdn.net/u012117917/article/details/41604711
# https://regexr.com/
re_config = {
    '(项目((?!名称|<\/).)*名称)': r'<k style="background-color:red">\1</k>',
    '((总|招标)?(投资|金额|额))': r'<k style="background-color:green;color: white">\1</k>',
    '(标段)': r'<k style="background-color:yellow">\1</k>',
    '(要求)': r'<k style="background-color:aqua">\1</k>',
    '(开标)': r'<k style="background-color:fuchsia">\1</k>',
    '(资质)': r'<k style="background-color:navy;color: white">\1</k>',
    '(联合体)': r'<k style="background-color:lime">\1</k>',
    '(保证金)': r'<k style="background-color:darkorange">\1</k>',
    '((招标)?(代理)(机构)?)': r'<k style="background-color:darkgoldenrod;color: white">\1</k>',
}

# https://stackoverflow.com/questions/23861680/convert-spreadsheet-number-to-column-letter
# 1->A 2->B
def colnum_string(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

# 获取指定页面
def get_page(url):
    global app, wb
    global dir_path, re_config
    global xlsx_table_head
    global nrows
    # 请求数据
    resp = requests.get(url, headers, verify=False)
    soup = BeautifulSoup(resp.content.decode('utf-8'), "html.parser")
    # 删除 top、bottom、script
    for top in soup.find_all("div", {'class': 'top'}):
        top.decompose()
    for bottom in soup.find_all("div", {'class': 'bottom'}):
        bottom.decompose()
    for script in soup.find_all("script"):
        script.decompose()
    # 使样式 CSS 文件正常加载
    for link in soup.find_all("link"):
        link['href'] = 'https://ggzy.hengyang.gov.cn' + link['href']
    content = str(soup)
    # 正则替换
    for patern, replacement in re_config.items():
        content = re.sub(patern, replacement, content)
    # 持久化：HTML
    file_name = re.search('(?<=\/)([^/]*.html)', url).group(1)
    file_path = os.path.join(dir_path, file_name)
    f = open(file_path, 'w', encoding="utf8")
    f.writelines(content)
    f.close()
    # 持久化：Excel
    row_data = ['']*len(xlsx_table_head)
    title_h3 = soup.select('.finalTitle>h3')[0].text
    title_p = soup.select('.finalTitle>p')[0].text
    update_date = re.search('(?<=发布时间：)(.*)', title_p).group(1)
        # 写入普通数据
    page_xlsx_data = {'发布时间': update_date, '公告名称': title_h3}
    for k, v in page_xlsx_data.items():
        index = xlsx_table_head.index(k)
        if not index < 0:
            row_data[index] = v
    nrows = nrows + 1
    sheet1[nrows-1, 0].value = row_data
        # 写入超链接
    page_xlsx_data = {'网页链接': url, '本地网页链接': file_path}
    for k, v in page_xlsx_data.items():
        index = xlsx_table_head.index(k)
        if not index < 0:
            sheet1[nrows-1, index].add_hyperlink(v)

# 获取页面
def get_pages(params):
    global app, wb, sheet1
    global nrows, ncols
    global xlsx_table_head
    url = 'https://ggzy.hengyang.gov.cn/jyxx/jsgcjy/zbgg/'
    # 写入表头
    nrows = nrows + 1
    sheet1[0,0].value = xlsx_table_head
    # 获取链接
    page_links = []
    for i in range(params['page']):
        if i == 0:
            resp = requests.get(url, headers, verify=False)
        else:
            resp = requests.get('{url}pages/{i}.html'.format(url=url, i=i+1), headers, verify=False)
        time.sleep(0.5)
        soup = BeautifulSoup(resp.content.decode('utf-8'), "html.parser")
        for el in soup.select('.nyLine a'):
            page_links.append(el['href'])
    # 获取指定页面
    for link in page_links:
        get_page(link)
        print(link)
        time.sleep(0.5)
    # 整理、退出
    prettify_excel()
    wb.save()
    wb.close()
    app.quit()

# 整理 Excel
def prettify_excel():
    # 调整较长列列宽为固定值，并自动换行
    for col in [3, 17, 18]:
        col_str = colnum_string(col)
        target_col = sheet1.range(col_str+':'+col_str)
        target_col.api.WrapText = True
        target_col.column_width = 30
    sheet1.autofit('r')
    sheet1.autofit('c')
    # 第一行
    row_1 = sheet1.range('1:1')
    row_1.row_height = 25
    row_1.api.Font.Bold = True
    row_1.api.Font.Size = 11
    row_1.api.HorizontalAlignment = -4108

# 初始化
def init():
    print('目标网页：https://ggzy.hengyang.gov.cn/jyxx/jsgcjy/zbgg/')
    global dir_path
    global wb, app, sheet1
    # 创建文件夹
    current_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
    dir_path = fs.create_dir(current_time)
    # 初始化 Excel（程序不可见，只打开不新建工作薄，屏幕更新关闭）
    app = xw.App(visible=False, add_book=False)
    app.display_alerts = False
    app.screen_updating = False
    # 新建 data.xlsx
    wb = app.books.add()
    xlsx_path = os.path.join(dir_path, 'data.xlsx')
    wb.save(xlsx_path)
    sheet1 = wb.sheets[0]

# 获取参数
def get_params():
    params = {}
    params['page'] = int(input('输入获取页数：'))
    return params


if __name__ == '__main__':
    try:
        init()
        params = get_params()
        get_pages(params)
    except Exception as ex:
        traceback.print_exc()
        # 关闭文件（不保存）、退出 Excel 程序
        try:
            wb.close()
            app.quit()
        except:
            pass
