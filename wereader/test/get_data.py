import request
import json

headers = {
    'Host': 'i.weread.qq.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    'Cookie':''
}

USERVID = 0

"""由url请求数据"""
def request_data(url):
    global headers
    r = requests.get(url,headers=headers,verify=False)
    if r.ok:
        data = r.json()
    else:
        raise Exception(r.text)
    return data

if __name__ == '__main__':
    bookId = input('bookId：')
    bookmarklist_url = "https://i.weread.qq.com/book/bookmarklist?bookId=" + bookId
    my_MPthought_url = 'https://i.weread.qq.com/review/list?listtype=6&mine=1&bookId=' + bookId + '&synckey=0&listmode=0'
    my_bookthought_url = "https://i.weread.qq.com/review/list?bookId=" + bookId + "&listType=11&mine=1&synckey=0&listMode=0"
    best_bookmark_url = "https://i.weread.qq.com/book/bestbookmarks?bookId=" + bookId
    bookInfo_url = "https://i.weread.qq.com/book/info?bookId=" + bookId
    book_shelf_url = "https://i.weread.qq.com/shelf/sync?userVid=" + str(USERVID) + "&synckey=0&lectureSynckey=0"
    data = request_data(bookmarklist_url)
    print(data)