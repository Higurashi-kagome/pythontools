""" 一个爬取图片的例子，用的是很基础的方法，下载速度不快，供学习 """

import os
import requests  # 先导入爬虫的库
from lxml import html

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
}  # 设置头部信息,伪装浏览器
host = "https://bing.ioliu.cn"  # 爬取这个网站上的图片
p = 1  # 记录当前页码

while True:
    response = requests.get(host, headers=headers, params={p: p})
    response.encoding = "utf-8"
    htree = html.fromstring(response.content)

    downloadHref = htree.xpath(
        '//*[contains(concat( " ", @class, " " ), concat( " ", "download", " " ))]/@href')  # 获取下载链接（链接不完整）
    page = htree.xpath(
        '//*[contains(concat( " ", @class, " " ), concat( " ", "page", " " ))]//span/text()')[0].split(' / ')  # 获取页码信息
    hasNext = page[0] != page[1]  # 是否还有下一页
    dir = os.getcwd() + "\\第" + str(p) + "页\\"  # 文件夹

    os.makedirs(dir)  # 创建文件夹
    for href in downloadHref:  # 遍历下载链接
        href = host + href
        pictrueResponse = requests.get(
            url=href, headers=headers)  # get方法的到图片响应
        fileName = href.split("/")[4].split("?")[0] + ".png"
        with open(dir + fileName, "wb+") as file:  # 打开一个文件,wb表示以二进制格式打开一个文件只用于写入
            file.write(pictrueResponse.content)  # 写入文件
            print(fileName)

    if not hasNext:
        print('已无下一页，程序结束。')
        os._exit(0)
    if input('第 ' + str(p) + ' 页下载完毕，是否继续？（y/n）') == "n":
        break
    p = p + 1   #更新页码
