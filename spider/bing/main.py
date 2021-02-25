""" 下载 https://bing.ioliu.cn 中的图片 """

import os
import requests
from lxml import html
import re

def main():
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36"
    }
    host = "https://bing.ioliu.cn"
    page_index = 1  # 记录当前页码

    while True:
        response = requests.get(host, headers=headers, params={"p": page_index})
        response.encoding = "utf-8"
        htree = html.fromstring(response.content)

        dir_name = "第 {} 页".format(page_index)
        os.makedirs(dir_name)
        downloadHref = htree.xpath(
            '//*[contains(concat( " ", @class, " " ), concat( " ", "download", " " ))]/@href')  # 获取下载链接（不完整）
        for href in downloadHref:  # 遍历下载链接
            url = host + href
            pictrueResponse = requests.get(url=url, headers=headers)  # get方法的到图片响应
            file_name ="{}.png".format(re.split('/|\?', url)[4])
            with open(os.path.join(dir_name, file_name), "wb+") as file:  # 打开一个文件，wb 表示以二进制格式打开一个文件只用于写入
                file.write(pictrueResponse.content)  # 写入文件
                print(file_name)

        page = htree.xpath(
            '//*[contains(concat( " ", @class, " " ), concat( " ", "page", " " ))]//span/text()')[0].split(' / ')  # 获取页码信息
        if page[0] == page[1]:
            print('已无下一页，程序结束。')
            os._exit(0)
        if input('第 {} 页下载完毕，是否继续？（y/n）'.format(page_index)) == "n":
            break
        page_index = page_index + 1   #更新页码

if __name__ == '__main__':
    main()
