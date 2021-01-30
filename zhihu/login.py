import os
import sys
import requests
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
requests.packages.urllib3.disable_warnings()

headers = {
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

cookie_file = os.getcwd() + "\\temp\\cookie.txt"

class MainWindow(QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.DomainCookies = {}

        self.setWindowTitle('知乎') # 设置窗口标题
        self.resize(900, 600) # 设置窗口大小
        self.setWindowFlags(Qt.WindowMinimizeButtonHint) # 禁止最大化按钮
        self.setFixedSize(self.width(), self.height()) # 禁止调整窗口大小

        self.browser = QWebEngineView() # 实例化浏览器对象

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.cookieStore().deleteAllCookies() # 初次运行软件时删除所有 cookies
        self.profile.cookieStore().cookieAdded.connect(self.onCookieAdd) # cookies 增加时触发 self.onCookieAdd() 函数

        self.browser.loadFinished.connect(self.onLoadFinished) # 网页加载完毕时触发 self.onLoadFinished() 函数

        url = 'https://www.zhihu.com/' # 目标地址
        self.browser.load(QUrl(url)) # 加载网页
        self.setCentralWidget(self.browser) # 设置中心窗口


    # 网页加载完毕事件
    def onLoadFinished(self):

        global headers

        # 获取 cookies
        cookies = ['{}={};'.format(key, value) for key,value in self.DomainCookies.items()]
        cookies = ' '.join(cookies)
        # 添加 Cookie 到 header
        headers.update(Cookie=cookies)
        # 判断是否成功登录
        if login_success(headers):
            #判断 temp 文件夹是否存在，不存在则创建
            temp_dir = os.getcwd() + "\\temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            #登录成功后写入 cookie
            with open(cookie_file, 'w',encoding='utf-8') as f:
                f.write(cookies)
            print('登录成功!')
            self.close()
        else:
            self.profile.cookieStore().deleteAllCookies()
            print('请登录知乎...')


    # 添加 cookies 事件
    def onCookieAdd(self, cookie):
        if 'www.zhihu.com' in cookie.domain() or 'zhihu.com' in cookie.domain():
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

def login_success(headers):
    """判断是否登录成功"""
    url = "https://www.zhihu.com/question/waiting"
    r = requests.get(url,headers=headers,verify=False)
    if '等你来答' in r.text:
        return True
    else:
        return False

def main():
    global headers
    # cookie 文件存在时尝试从文件中读取 cookie 登录
    if os.path.exists(cookie_file) and os.path.isfile(cookie_file):
        #读取
        headers_from_file = {}
        with open(cookie_file,'r',encoding='utf-8') as f:
            cookie_lines = f.readlines()
            if len(cookie_lines) == 1 and cookie_lines[0]:# 如果 cookie 文件不为空
                headers_from_file = headers
                headers_from_file.update(Cookie=cookie_lines[0])
        # 尝试登陆
        if login_success(headers_from_file):
            print('登录成功!')
            #登录成后更新 headers
            headers = headers_from_file
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
    print('**********************************************************')
    return True

if __name__=='__main__':
    main()