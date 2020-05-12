#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
@file: main.py
@author: liuhao326
@time: 2020/5/11 21:14
"""

from wereader import *
from wereader import level1,level2,level3,style1,style2,style3
from wereader import USERVID,headers,thought_style,way_to_append
import sys
import os
import time
import pyperclip
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile

# 微信读书用户id
USERVID = 0
# 文件路径
file=''
cookie_file = os.getcwd() + "\\temp\\cookie.txt"
"""追加内容到文件"""
def push_to_file(res):
    global file
    if file == '':
        file = input('请输入文件路径，内容将会追加到该文件中：').replace('\\','\\\\')
        if len(file) > 0 and os.path.exists(file) and os.path.isfile(file):
            with open(file, 'a',encoding='utf-8') as f:
                f.write(res)
                print('push完成')
        elif file != '':
            print('**无效路径，未写入文件**')
            file = ''
    elif len(file) > 0 and os.path.exists(file) and os.path.isfile(file):
        print('当前文件路径为：' + file)
        with open(file, 'a',encoding='utf-8') as f:
            f.write(res)
            print('push完成')

"""输出内容并复制到剪切板"""
def print_and_copy(res):
    print(res)
    pyperclip.copy(res)

"""获取标注(md)"""
def get_mark(bookId):
    is_print_all = input('选择：所有标注/指定章节的标注(1/2)?\n')
    if is_print_all.strip() == '1':#如果选择输出所有标注
        way_to_print_chapter = input('选择：包含所有标题/只包含有标注的标题(1/2)?\n')
        if way_to_print_chapter.strip() == '1':#如果选择输出所有标题
            res = get_bookmarklist(bookId)
        elif way_to_print_chapter.strip() == '2':#如果选择只输出包含标注的标题
            res = get_bookmarklist(bookId,is_all_chapter = 0)
        else:
            print('其他指令，默认包含所有标题\n')
            res = get_bookmarklist(bookId)
    elif is_print_all.strip() == '2':#如果选择输出指定章节的标注
        sorted_chapters = get_sorted_chapters(bookId)
        for chapter in sorted_chapters:
            print(str(chapter[0]) + ' '*(5 - len(str(chapter[0]))) + chapter[2])
        chapterUid = int(input('输入章节ID：\n'))
        res = get_bookmarklist(bookId,is_all_chapter = 1,chapterUid=chapterUid)
    else:
        print('其他指令，默认包含所有标注\n')
        res = get_bookmarklist(bookId)
    return res

"""打印提示、返回输入"""
def print_guide():
    print_choice = [
        '输出标注：print 1',
        '输出想法：print 2',
        '输出热门标注：print 3',
        '输出书本目录：print 4',
        '输出书本信息：print 5',
        '输出个人最新标注：print 6',
        '按文档树输出书架中的书：print 7',
        '直接输出书架中的书：print 8'
            ]
    push_choice = [
        '推送标注：push 1',
        '推送想法：push 2',
        '推送热门标注：push 3',
        '推送书本目录：push 4',
        '推送书本信息：push 5',
        '推送个人最新标注：push 6'
            ]
    setting_choice = [
        '重新设置书本ID：change id',
        '设置文件路径：change file',
        '设置新标注追加模式：append mode'
            ]
    #开始打印
    print('输入命令调用函数：')
    print('*******print*******')
    for choice in print_choice:
        print(choice)
    print('*******push********')
    for choice in push_choice:
        print(choice)
    print('******setting******')
    for choice in setting_choice:
        print(choice)
    print('输入exit退出')
    y = input()
    return y

"""根据输入调用相应函数"""
def main(bookId):
    global file
    global way_to_append
    bookId = bookId
    while True:
        y = print_guide().replace(' ','').lower()
        if y[:-1] == 'print':
            if y == 'print1':
                res = get_mark(bookId)
                print_and_copy(res)
                print('**********************************************************')
            elif y == 'print2':
                res = get_mythought(bookId)
                print_and_copy(res)
                print('**********************************************************')
            elif y == 'print3':
                res = get_bestbookmarks(bookId)
                print_and_copy(res)
                print('**********************************************************')
            elif y == 'print4':
                res = '\n'
                sorted_chapters = get_sorted_chapters(bookId)
                for chapter in sorted_chapters:
                    res += set_chapter_level(chapter[1]) + ' ' + chapter[2] + '\n\n'
                print_and_copy(res)
                print('**********************************************************')
            elif y == 'print5':
                res = get_bookinfo(bookId)
                print_and_copy(res)
                print('**********************************************************')
            elif y == 'print6':
                if way_to_append == '':
                    way_to_append = input('选择追加模式：按时间/按位置(1/2)?').replace(' ','')
                elif way_to_append.strip() == '1':
                    line_and_res = get_new_content_bytime(bookId)
                    print_and_copy(line_and_res[1])
                elif way_to_append.strip() == '2':
                    line_and_res = get_new_content_byrange(bookId)
                    print_and_copy(line_and_res[1])
                else:
                    print('输入无效')
            elif y == 'print7':
                print_books_as_tree(userVid=USERVID)
                print('**********************************************************')
            elif y == 'print8':
                print_books_directly(userVid=USERVID)
                print('**********************************************************')
        elif y[:-1] == 'push':
            if y == 'push1':
                res = get_mark(bookId)
                push_to_file(res)
                print('**********************************************************')
            elif y == 'push2':
                res = get_mythought(bookId)
                push_to_file(res)
                print('**********************************************************')
            elif y == 'push3':
                res = get_bestbookmarks(bookId)
                push_to_file(res)
                print('**********************************************************')
            elif y == 'push4':
                res = '\n'
                sorted_chapters = get_sorted_chapters(bookId)
                for chapter in sorted_chapters:
                    res += set_chapter_level(chapter[1]) + ' ' + chapter[2] + '\n\n'
                push_to_file(res)
                print('**********************************************************')
            elif y == 'push5':
                res = get_bookinfo(bookId)
                push_to_file(res)
                print('**********************************************************')
            elif y == 'push6':
                if way_to_append == '':
                    way_to_append = input('选择追加模式：按时间/按位置(1/2)?').replace(' ','')
                elif way_to_append.strip() == '1':
                    line_and_res = get_new_content_bytime(bookId)
                    #检查返回内容是否有效
                    if line_and_res[0] == '':
                        continue
                    print('将' + line_and_res[0] + '后的新内容push到文件')
                    push_to_file(line_and_res[1])
                elif way_to_append.strip() == '2':
                    line_and_res = get_new_content_byrange(bookId)
                    #检查返回内容是否有效
                    if line_and_res[0] == '':
                        continue
                    print('将' + line_and_res[0] + '后的新内容push到文件')
                    push_to_file(line_and_res[1])
                else:
                    print('输入无效')
        elif y == 'exit':
            return 0
        elif y == 'changeid':
            return 1
        elif y == 'changefile':
            f = input('请输入文件路径，内容将会追加到该文件中：').replace('\\','\\\\')
            if len(f) > 0 and os.path.exists(f) and os.path.isfile(f):
                file = f
                print('设置成功')
            else:
                print('无效路径')
        elif y == 'appendmode':
            append_mode = input('选择追加模式：按时间/按位置(1/2)?').replace(' ','')
            if append_mode in ['1','2']:
                way_to_append = append_mode
                print('设置成功')
            else:
                print('输入无效')
        else:
            print('输入无效')
        
class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.DomainCookies = {}

        self.setWindowTitle('微信读书助手') # 设置窗口标题
        self.resize(900, 600) # 设置窗口大小
        self.setWindowFlags(Qt.WindowMinimizeButtonHint) # 禁止最大化按钮
        self.setFixedSize(self.width(), self.height()) # 禁止调整窗口大小

        url = 'https://weread.qq.com/#login' # 目标地址
        self.browser = QWebEngineView() # 实例化浏览器对象

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.cookieStore().deleteAllCookies() # 初次运行软件时删除所有cookies
        self.profile.cookieStore().cookieAdded.connect(self.onCookieAdd) # cookies增加时触发self.onCookieAdd()函数

        self.browser.loadFinished.connect(self.onLoadFinished) # 网页加载完毕时触发self.onLoadFinished()函数

        self.browser.load(QUrl(url)) # 加载网页
        self.setCentralWidget(self.browser) # 设置中心窗口





    # 网页加载完毕事件
    def onLoadFinished(self):

        global USERVID
        global headers

        # 获取cookies
        cookies = ['{}={};'.format(key, value) for key,value in self.DomainCookies.items()]
        cookies = ' '.join(cookies)
        # 添加Cookie到header
        headers.update(Cookie=cookies)
        # 判断是否成功登录微信读书
        if login_success(headers):
            #判断temp文件夹是否存在，不存在则创建
            temp_dir = os.getcwd() + "\\temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            #登录成功后写入cookie
            with open(cookie_file, 'w',encoding='utf-8') as f:
                f.write(cookies)
            print('登录微信读书成功!')
            # 获取用户user_vid
            if 'wr_vid' in self.DomainCookies.keys():
                USERVID = self.DomainCookies['wr_vid']
                print('用户id:{}'.format(USERVID))
                # 关闭整个qt窗口
                self.close()

        else:
            self.profile.cookieStore().deleteAllCookies()
            print('请扫描二维码登录微信读书...')




    # 添加cookies事件
    def onCookieAdd(self, cookie):
        if 'weread.qq.com' in cookie.domain():
            name = cookie.name().data().decode('utf-8')
            value = cookie.value().data().decode('utf-8')
            if name not in self.DomainCookies:
                self.DomainCookies.update({name: value})




    # 窗口关闭事件
    def closeEvent(self, event):
        """
        重写closeEvent方法，实现窗体关闭时执行一些代码
        :param event: close()触发的事件
        :return: None
        """

        self.setWindowTitle('退出中……')  # 设置窗口标题
        self.profile.cookieStore().deleteAllCookies()

if __name__=='__main__':
    #cookie文件存在时尝试从文件中读取cookie登录
    if os.path.exists(cookie_file) and os.path.isfile(cookie_file):
        with open(cookie_file,'r',encoding='utf-8') as f:
            cookie_in_file = f.readlines()
        headers_frome_file = headers
        headers_frome_file.update(Cookie=cookie_in_file[0])
        if login_success(headers_frome_file):
            print('登录微信读书成功!')
            #获取用户user_vid
            for item in cookie_in_file[0].split(';'):
                if item.strip()[:6] == 'wr_vid':
                    USERVID = int(item.strip()[7:])
        else:
            app = QApplication(sys.argv) # 创建应用
            window = MainWindow() # 创建主窗口
            window.show() # 显示窗口
            app.exec_() # 运行应用，并监听事件
    #文件不存在时再启用登录界面
    else:
        app = QApplication(sys.argv) # 创建应用
        window = MainWindow() # 创建主窗口
        window.show() # 显示窗口
        app.exec_() # 运行应用，并监听事件
    
    
    #将书架按{bookId1:"title1"...}的形式储存在字典中
    bookId_dict = get_bookshelf(userVid=USERVID,list_as_shelf = False)
    print('**********************************************************')
    while True:
        print_books_as_tree(userVid=USERVID)
        #提示输入书本id，正确输入后进入主函数
        bookId = input('请输入书本ID：\n')
        if bookId.strip() in bookId_dict.keys():
            y = main(bookId)
            if y == 0:
                break
            elif y == 1:
                continue
