""" 建标库规范 selenium 自动化下载 """

from selenium import webdriver
import requests
import time
from PIL import Image
from fpdf import FPDF
import os
import re
import win32api
from win10toast import ToastNotifier

""" 弹窗提示 """
def alert(msg, title):
    win32api.MessageBox(0, msg, title, 0x00001000) 

""" 图片转 PDF """
def imagesToPdf(img_paths, pdf_save_path, pdf_name):
    pdf_path = os.path.join(pdf_save_path, '{}.pdf'.format(pdf_name))

    pdf = FPDF()
    for imageFile in img_paths:
        cover = Image.open(imageFile)
        width, height = cover.size

        # convert pixel in mm with 1px=0.264583 mm
        # width, height = float(width * 0.264583), float(height * 0.264583)

        # given we are working with A4 format size 
        pdf_size = {'P': {'w': 210, 'h': 297}, 'L': {'w': 297, 'h': 210}}

        # get page orientation from image size 
        orientation = 'P' if width < height else 'L'

        #  make sure image size is not greater than the pdf format size
        width = width if width < pdf_size[orientation]['w'] else pdf_size[orientation]['w']
        height = height if height < pdf_size[orientation]['h'] else pdf_size[orientation]['h']

        pdf.add_page(orientation=orientation)

        pdf.image(imageFile, 0, 0, width, height)
    pdf.output(pdf_path, "F")

""" 下载图片 """
def download_images(startUrl):

    # 创建用于保存所有图片的文件夹
    cur_path = os.path.abspath(os.path.dirname(__file__))
    img_save_path = os.path.join(cur_path, 'images')
    if not os.path.exists(img_save_path):
        os.makedirs(img_save_path)

    # 添加配置防止打印一些无用的日志
    options = webdriver.ChromeOptions()
    options.add_experimental_option(
        "excludeSwitches", ['enable-automation', 'enable-logging'])
    driver = webdriver.Chrome(options=options,executable_path=r'../../utils/chromedriver.exe')
    driver.implicitly_wait(30)
    # 打开网页
    driver.get(startUrl)
    
    # 获取规范名
    file_name = driver.find_element_by_xpath(
        '//div[@class="location"]/span/a[last()]').text
    # 去除特殊字符，防止创建文件夹失败
    file_name = re.sub(r'\||\<|\>|\\|\/|\:|\*|\"|\?','-',file_name.strip())

    # 创建保存某一规范的文件夹
    img_save_path = os.path.join(img_save_path, file_name)
    if not os.path.exists(img_save_path):
        os.makedirs(img_save_path)

    # 正式下载
    print(file_name)
    next_btn = driver.find_element_by_css_selector('.next_catalog a')
    page_total = len(driver.find_elements_by_css_selector('.catalog_name a'))
    img_paths = []
    while True:
        # 获取图片地址。会出现需要输入验证码的情况
        try:
            img_src = driver.find_element_by_css_selector(
                '.book-content-show img').get_attribute('src')
        except Exception as ex:
            # 置于最顶层的通知消息
            alert('出现验证码，请在网页中输入验证码后在命令行回车继续','验证码')
            input('验证成功后在此回车以继续下载')
            img_src = driver.find_element_by_css_selector(
                '.book-content-show img').get_attribute('src')
            # 页面已更新，需要重新获取对象
            next_btn = driver.find_element_by_css_selector('.next_catalog a')

        # 请求图片内容
        try:
            # timeout 参数解决报错：“由于连接方在一段时间后没有正确答复或连接的主机没有反应，连接尝试失败”
            rsp = requests.get(img_src, timeout=(3,7))
        except Exception as ex:
            alert('图片下载失败', '出错')
            raise(ex)
        
        # 获取页面标题
        selected_page = driver.find_element_by_css_selector('.li_selected a')
        page_title = selected_page.get_attribute('title')
        print(f'{page_title}/共 {page_total} 页\r',end='')

        # 将获取到的图片二进制流写入本地文件
        img_path = os.path.join(img_save_path, '{}.jpg'.format(page_title))
        with open(img_path, 'wb') as f:
            f.write(rsp.content)
            img_paths.append(img_path)
        
        # 判断是否到达最后一页
        try:
            # 捕捉网页需要输入验证码，且用户在程序等待用户输入之前进行验证时出现的报错
            title = next_btn.get_attribute('title')
        except Exception as ex:
            next_btn = driver.find_element_by_css_selector('.next_catalog a')
            title = next_btn.get_attribute('title')
        if title == '下一章：没有了':
            break
        else:
            next_btn.click()
            time.sleep(1)
            # 调用 click 后 DOM 已发生变化，需要重新获取
            next_btn = driver.find_element_by_css_selector('.next_catalog a')

    # 下载结束，退出
    driver.quit()
    return img_paths, img_save_path, file_name

if __name__ == '__main__':
    # startUrl = 'http://www.jianbiaoku.com/webarbs/book/11485/510880.shtml'
    # startUrl = 'http://www.jianbiaoku.com/webarbs/book/11173/1039966.shtml'
    startUrl = input('输入 url：')
    
    # 下载图片（得到图片路径、PDF 保存路径和规范名）
    img_paths, pdf_save_path, pdf_name = download_images(startUrl)

    # 图片保存为 PDF
    imagesToPdf(img_paths, pdf_save_path, pdf_name)

    toaster = ToastNotifier()
    toaster.show_toast("下载完成"," ")

    # 支持非图片格式下载
    # 提示是否删除图片
    # 关闭图片加载？应该不行，因为会有验证码需要填
    # 支持检查 Chrome driver 配置状态，未配置好则不执行并结束程序
    # 处理图片大小不一致导致导致图片超出 PDF 页面的问题√

""" 参考 """
# [python FPDF not sizing correctly - Stack Overflow](https://stackoverflow.com/questions/43767328/python-fpdf-not-sizing-correctly)
# [Alert boxes in Python? - Stack Overflow](https://stackoverflow.com/questions/177287/alert-boxes-in-python)
# [建标库(JianBiaoKu.com)图片数据转PDF爬虫案例_Test_Box-CSDN博客](https://blog.csdn.net/joson1234567890/article/details/105138707)
# [Python glob.glob always returns empty list - Stack Overflow](https://stackoverflow.com/questions/37619246/python-glob-glob-always-returns-empty-list)
# [Selenium下载页面上的图片_小满测试-CSDN博客_selenium 下载图片](https://blog.csdn.net/minzhung/article/details/102510142)