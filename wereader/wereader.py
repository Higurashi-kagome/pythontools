import json
import os
import sys
import requests
from collections import defaultdict

requests.packages.urllib3.disable_warnings()
level1 = '## '#(微信读书)一级标题
level2 = '### '#二级标题
level3 = '#### '#三级标题
style1 = {'pre': "",   'suf': ""}#(微信读书)红色下划线
style2 = {'pre': "**",   'suf': "**"}#橙色背景色
style3 = {'pre': "",   'suf': ""}#蓝色波浪线
thought_style = {'pre': "```\n",   'suf': "\n```"}#想法前后缀
hotmarks_number = {'pre': "`",   'suf': "`  "}#热门标注标注人数前后缀
way_to_append = ''
comment_mode = ''
USERVID = 0

headers_p = {
    'Connection': 'keep-alive',
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Content-Type': 'application/json;charset=UTF-8',
    'Origin': 'https://weread.qq.com',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 设置header
headers = {
    'Host': 'i.weread.qq.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

def set_content_style(style,text):
    global style1,style2,style3
    if style == 0:#红色下划线
        return style1['pre'] + text.strip() + style1['suf']
    elif style == 1:#橙色背景色
        return style2['pre'] + text.strip() + style2['suf']
    elif style == 2:#蓝色波浪线
        return style3['pre'] + text.strip() + style3['suf']

def set_chapter_level(level):
    global level1,level2,level3
    if level == 1:
        return level1
    elif level == 2:
        return level2
    elif level == 3:
        return level3

def set_thought_style(text):
    global thought_style
    return thought_style['pre'] + text + thought_style['suf']

def set_hotmarks_number(number):
    global hotmarks_number
    return hotmarks_number['pre'] + str(number) + hotmarks_number['suf']

"""由url请求数据"""
def request_data(url):
    global headers
    r = requests.get(url,headers=headers,verify=False)
    if r.ok:
        data = r.json()
    else:
        raise Exception(r.text)
    return data

"""
(按顺序)获取书中的章节：
[(1, 1, '封面'), (2, 1, '版权信息'), (3, 1, '数字版权声明'), (4, 1, '版权声明'), (5, 1, '献给'), (6, 1, '前言'), (7, 1, '致谢')]
"""
def get_sorted_chapters(bookId):
    if '_' in bookId:
        print('公众号不支持输出目录')
        return ''
    url = "https://i.weread.qq.com/book/chapterInfos?" + "bookIds=" + bookId + "&synckeys=0"
    data = request_data(url)
    chapters = []
    #遍历章节,章节在数据中是按顺序排列的，所以不需要另外排列
    for item in data['data'][0]['updated']:
        #判断item是否包含level属性。
        try:
            chapters.append((item['chapterUid'],item['level'],item['title']))
        except:
            chapters.append((item['chapterUid'],1,item['title']))
    """chapters = [(1, 1, '封面'), (2, 1, '版权信息'), (3, 1, '数字版权声明'), (4, 1, '版权声明'), (5, 1, '献给'), (6, 1, '前言'), (7, 1, '致谢')]"""
    return chapters

"""
获取以章节id为键，以排序好的标注列表为值的字典：
{"chapterUid":[[text_positon1,style1,"text1"],[text_positon2,style2,"text2"]...]}
"""
def get_sorted_contents_from_data(data):
    bookId = data['book']['bookId']
    #书本为公众号的情况{createTime:[[text_position1,'text1'],...]}
    if '_' in bookId:
        sorted_content = []  #
        marks = defaultdict(list)   #{'refMpReviewId':[[position,'text'],...],...}
        chapters = defaultdict(list) #{createTime:['reviewId','title'],...}
        i = 0
        for refMpInfos in data['refMpInfos']:
            chapters[i] = [refMpInfos['reviewId'],refMpInfos['title']]
            i = i + 1
        #排序得到[(createTime1,['revieId1','title1']),...]
        sorted_chapters = sorted(chapters.items())
        #获得{createTime1:[[text_position1,'text1'],...],...}
        for item in data['updated']:
            marks[item['refMpReviewId']].append([int(item['range'].split('-')[0]),item['markText']])
        #排序得到{'refMpReviewId':[[position1,'title1'],...]...}
        sorted_marks = {}
        for key in marks.keys():
            sorted_marks[key] =  sorted(marks[key],key=lambda x: x[0])
        #遍历章节
        for chapter in sorted_chapters:
            sorted_content.append({chapter[1][1]:sorted_marks[chapter[1][0]]})
        return sorted_content
        
    contents = defaultdict(list)
    """遍历所有标注并添加到字典储存起来"""
    for item in data['updated']:#遍历标注
        #获取标注的章节id
        chapterUid = item['chapterUid']
        #获取标注的文本内容
        text = item['markText']
        #获取标注开始位置用于标记位置
        text_position = int(item['range'].split('-')[0])
        text_style = item['style']
        #以章节id为键，以章内标注构成的列表为值,获得{"chapterUid":{text_positon:"text"}}
        contents[chapterUid].append([text_position,text_style,text])
    """将每章内的标注按键值排序，得到sorted_contents = {"chapterUid":[[text_positon2,style2,"text2"],[text_positon1,style1,"text1"]...]}"""
    sorted_contents = defaultdict(list)
    for chapterUid in contents.keys():
        #标注按位置排序，获得：
        #{"chapterUid":[[text_positon1,style1,"text1"],[text_positon2,style2,"text2"]...]}
        sorted_contents[chapterUid] = sorted(contents[chapterUid],key=lambda x: x[0])
    return sorted_contents

"""
(按顺序)返回data数据中的标注(Markdown格式)，标注标题按级别设置，标注内容设置前后缀
"""
def get_md_str_from_data(data,is_all_chapter=1):
    res = '\n'
    bookId = data['book']['bookId']
    #书本为公众号的情况
    if '_' in bookId:
        sorted_contents = get_sorted_contents_from_data(data)
        #遍历章节
        for chapter in sorted_contents:
            #获得章节标题和标注
            for title,marks in chapter.items():
                res += '### ' + title + '\n\n'
                #遍历标注
                for mark in marks:
                    res += mark[1] + '\n\n'
        return res
    #获取章节和标注
    sorted_chapters = get_sorted_chapters(bookId)
    sorted_contents = get_sorted_contents_from_data(data)
    #遍历章节
    for chapter in sorted_chapters:#chapter = (chapterUid,position,title)
        #如果指明不输出所有标题
        if is_all_chapter <= 0 and len(sorted_contents[chapter[0]]) == 0:
            continue
        #获取章节名
        title = chapter[2]
        res += set_chapter_level(chapter[1]) + title + '\n\n'
        #遍历一章内的标注
        for text in sorted_contents[chapter[0]]:#text = [position,style,markText]
            res += set_content_style(text[1],text[2]) + '\n\n'
    return res

"""
(按顺序)获取书中的标注(Markdown格式、标题分级、标注前后缀)
"""
def get_bookmarklist(bookId,is_all_chapter=1,chapterUid=-5):
    """获取笔记返回md文本"""
    #请求数据
    url = "https://i.weread.qq.com/book/bookmarklist?bookId=" + bookId
    data = request_data(url)
    if '_' in bookId:
        res = get_md_str_from_data(data)
        if res == '':#如果在书本中未找到标注
            print('书中无标注/获取出错')
            return ''
        return res
    """处理数据，生成笔记"""
    res = ''
    if chapterUid < 0:#生成全部标注
        res = get_md_str_from_data(data,is_all_chapter = is_all_chapter)
        if res == '':#如果在书本中未找到标注
            print('书中无标注/获取出错')
            return ''
    else:#如果传入了chapterUid，生成指定章节的标注
        sorted_chapters = get_sorted_chapters(bookId)
        #遍历章节
        for chapter in sorted_chapters:
            if chapter[0] == chapterUid:#找到指定章节
                #获取章节名
                title = chapter[2]
                res += set_chapter_level(chapter[1]) + title + '\n\n'
                #遍历章内标注
                sorted_contents = get_sorted_contents_from_data(data)
                for text in sorted_contents[chapter[0]]:
                    res += set_content_style(text[1],text[2]) + '\n\n'
                break
        if res == '':#如果标注res无新内容（在书本中未找到指定章节）
            print('未找到该章节/获取出错')
            return ''
    return res

"""
(按顺序)获取书中的所有个人想法(Markdown格式,含原文,标题分级,想法前后缀)
"""
def get_mythought(bookId):
    res = ''
    """获取数据"""
    if '_' in bookId:
        url = 'https://i.weread.qq.com/review/list?listtype=6&mine=1&bookId=' + bookId + '&synckey=0&listmode=0'
        data = request_data(url)
        print('公众号暂时不支持获取想法')
        return ''
    else:
        url = "https://i.weread.qq.com/review/list?bookId=" + bookId + "&listType=11&mine=1&synckey=0&listMode=0"
        data = request_data(url)
        """ print(data)
        return """
    """遍历所有想法并添加到字典储存起来
    thoughts = {30: {7694: '...',122:'...'}, 16: {422: '...',}, 12: {788: '...',}}
    """
    thoughts = defaultdict(dict)
    MAX = 1000000000
    for item in data['reviews']:
        #获取想法所在章节id
        chapterUid = item['review']['chapterUid']
        #获取原文内容
        abstract = item['review']['abstract']
        #获取想法
        text = item['review']['content']
        #获取想法开始位置
        try:
            text_positon = int(item['review']['range'].split('-')[0])
        except:
            #处理在章末添加想法的情况(将位置设置为一个很大的值)
            text_positon = MAX + int(item['review']['createTime'])
        #以位置为键，以标注为值添加到字典中,获得{chapterUid:{text_positon:"text分开想法和原文内容abstract"}}
        thoughts[chapterUid][text_positon] = text + '分开想法和原文内容' + abstract
    
    """章节内想法按range排序
    thoughts_sorted_range = 
    {30: [(7694, '....')], 16: [(422, '...')], 12: [(788, '...')]}
    """
    thoughts_sorted_range = defaultdict(list)
    #每一章内的想法按想法位置排序
    for chapterUid in thoughts.keys():
        thoughts_sorted_range[chapterUid] = sorted(thoughts[chapterUid].items())
    
    """章节按id排序
    sorted_thoughts = 
    [(12, [(788, '...')]), (16, [(422, '...')]), (30, [(7694, '...')])]
    """
    sorted_thoughts = sorted(thoughts_sorted_range.items())
    
    """获取包含目录级别的目录数据"""
    #获取包含目录级别的全书目录[(chapterUid,level,'title')]
    sorted_chapters = get_sorted_chapters(bookId)
    #去除没有想法的目录项
    d_sorted_chapters = []
    for chapter in sorted_chapters:
        if chapter[0] in thoughts_sorted_range.keys():
            d_sorted_chapters.append(chapter)
    
    """生成想法"""
    for i in range(len(sorted_thoughts)):
        counter = 1
        res += set_chapter_level(d_sorted_chapters[i][1]) + d_sorted_chapters[i][2] + '\n\n'
        for thought in sorted_thoughts[i][1]:
            text_and_abstract = thought[1].split('分开想法和原文内容')
            #如果为章末发布的标注（不包含 abstract 的标注）
            if text_and_abstract[1] == '':
                text_and_abstract[1] = "章末想法" + str(counter)
                counter = counter + 1
            res += text_and_abstract[1] + '\n\n' + set_thought_style(text_and_abstract[0]) + '\n\n'
    if res.strip() == '':
        print('无想法')
    return res

"""
(按顺序)获取书中的所有热门标注(Markdown格式)
"""
def get_bestbookmarks(bookId):
    if '_' in bookId:
        print('公众号不支持热门标注')
        return ''
    """获取书籍的热门划线,返回文本"""
    url = "https://i.weread.qq.com/book/bestbookmarks?bookId=" + bookId
    data = request_data(url)
    
    """获取包含目录级别的目录数据"""
    #以章节id为键，以标题内容为值建立字典
    chapters = {c['chapterUid']:c['title'] for c in data['chapters']}
    #获取包含目录级别的全书目录[(chapterUid,level,'title')]
    sorted_chapters = get_sorted_chapters(bookId)
    #去除没有想法的目录项
    d_sorted_chapters = []
    for chapter in sorted_chapters:
        if chapter[0] in chapters.keys():
            d_sorted_chapters.append(chapter)
    
    """以章节id为键，以章内热门标注组成的字典为值建立字典"""
    contents = defaultdict(dict)
    for item in data['items']:
        #获取标注的章节id
        chapterUid = item['chapterUid']
        text = item['markText']
        text_position = int(item['range'].split('-')[0])
        text_number = set_hotmarks_number(item['totalCount'])
        contents[chapterUid][text_position] = text_number + text
    """章内热门标注按range排序"""
    sorted_contents = defaultdict(list)
    for chapterUid in contents.keys():
        sorted_contents[chapterUid] = sorted(contents[chapterUid].items())
    
    """获取字符串"""
    res = ''
    for chapter in d_sorted_chapters:
        title = chapter[2]
        res += set_chapter_level(chapter[1]) + title +'\n\n'
        for text in sorted_contents[chapter[0]]:
            res += text[1].strip() + '\n\n'
    if res.strip() == '':
        print('无热门标注')
    return res

"""
获取书本信息(Markdown格式)
"""
def get_bookinfo(bookId):
    if '_' in bookId:
        print('公众号不支持书本信息')
        return ''
    """获取书的详情"""
    url = "https://i.weread.qq.com/book/info?bookId=" + bookId
    data = request_data(url)
    bookinfo = [('title',data['title']),('author',data['author']),('category',data['category']),('introduction',data['intro']),('publisher',data['publisher'])]
    res = '\n'
    for item in bookinfo:
        res += item[0] + '：' + item[1] + '\n\n'
    return res

"""
(排序)获取书架中的书:
直接列出——[(readUpdateTime,['bookId',"bookName"]),...]
按分类列出——{'计算机':[[readUpdatetime,'bookId','title'],...]}
"""
def get_sorted_bookshelf(userVid=USERVID,list_as_shelf = True):
    url = "https://i.weread.qq.com/shelf/sync?userVid=" + str(userVid) + "&synckey=0&lectureSynckey=0"
    data = request_data(url)
    """获取书架上的所有书"""
    if list_as_shelf == True:   #分类列出
        #{'bookId':[readUpdatetime,'bookId',title]}
        books = {}
        for book in data['books']:
            bookId = book['bookId']
            books[bookId] = [book['readUpdateTime'],bookId,book['title']]
        #遍历书本分类：{'计算机':[[readUpdatetime,'bookId',title],...]}
        shelf = defaultdict(list)
        for archive in data['archive']:
            #遍历某类别内的书本id并追加[readUpdatetime,'bookId',title]
            for bookId in archive['bookIds']:
                shelf[archive['name']].append(books[bookId])
                del books[bookId]
        #附加未分类书本
        if books:
            for bookId in books.keys():
                shelf['未分类书本'].append(books[bookId])
        #排序
        for category in shelf.keys():
            shelf[category] = sorted(shelf[category],key=lambda x: x[0])
            shelf[category].reverse()
        return shelf
    else:   #直接列出
        #遍历所有书并储存到字典,得到{{readUpdateTime:['bookId',"bookName"]}}
        books = {}
        for book in data['books']:
            books[book['readUpdateTime']] = [book['bookId'],book['title']]
        #排序得到[(readUpdateTime,['bookId',"bookName"])]
        sorted_books = sorted(books.items())
        sorted_books.reverse()
        return sorted_books

"""
(不排序)获取书架中的书：
直接列出——{'bookId1':"title1"...}
按分类列出——{"计算机":{'bookId1':"bookName"...}...}
"""
def get_bookshelf(userVid=USERVID,list_as_shelf = True):
    url = "https://i.weread.qq.com/shelf/sync?userVid=" + str(userVid) + "&synckey=0&lectureSynckey=0" 
    data = request_data(url)
    """获取书架上所有书"""
    if list_as_shelf == True:   #分类列出
        #遍历所有书并储存到字典
        books = {}
        for book in data['books']:
            books[book['bookId']] = book['title']
        
        #遍历书架分类创建整个书架
        shelf = defaultdict(dict)
        #遍历书架分类
        for archive in data['archive']:
            #遍历书架分类内的书本id并赋值
            for bookId in archive['bookIds']:
                shelf[archive['name']][bookId] = books[bookId]
                del books[bookId]
        #附加未分类书本
        for bookId,bookName in books.items():
            shelf['未分类书本'][bookId] = bookName
        return shelf
    else:   #直接列出
        #遍历所有书并储存到字典
        books = {}
        for book in data['books']:
            books[book['bookId']] = book['title']
        return books

"""
获取评价
"""
def get_comment(bookId,mode = '1'):
    url = 'https://i.weread.qq.com/review/list?listType=6&synckey=0&userVid=' + str(USERVID) + '&rangeType=2&mine=1&listMode=1'
    data = request_data(url)
    #获取有评价的书籍列表并检查书本是否在其中
    books_have_comment = []
    for item in data['reviews']:
        if item['review']['content'] != "":
            book_id = item['review']['book']['bookId']
            books_have_comment.append(book_id)
    if bookId not in books_have_comment:
        print('无评价')
        return ''
    #获取评价并返回
    comment = ''
    for item in data['reviews']:
        book_id = item['review']['book']['bookId']
        if book_id == bookId:
            title = '### ' + item['review']['title']
            htmlContent = item['review']['htmlContent']
            content = item['review']['content']
            if mode == '2':
                comment = title + '\n\n' + htmlContent
            else:
                comment = title + '\n\n' + content
            return comment

def remove_bookmark(bookmarkId):
    global headers_p
    url = 'https://weread.qq.com/web/book/removeBookmark'
    d = {"bookmarkId":bookmarkId}
    r = requests.post(url,data = json.dumps(d),headers=headers_p,verify=False)
    if r.ok:
        data = r.json()
        if data['succ'] == 1:
            print(bookmarkId + '：ok')
        else:
            print(bookmarkId + '：fail')
    else:
        raise Exception(r.text)

def remove_all_bookmark(bookId):
    if '_' in bookId:
        print('公众号暂不支持删除标注')
        return
    #请求标注数据
    url = "https://i.weread.qq.com/book/bookmarklist?bookId=" + bookId
    data = request_data(url)
    #遍历bookmarkId删除标注
    for item in data['updated']:
        bookmarkId = item['bookmarkId']
        remove_bookmark(bookmarkId)


"""直接输出书架中的书：bookId bookName"""
def print_books_directly(userVid=USERVID):
    books = get_sorted_bookshelf(userVid,False)
    for book in books:
        book_id = book[1][0]
        book_name = book[1][1]
        print(book_id + ' '*(10 - len(book_id)) + ' ' + book_name)
    return ''

"""按分类输出，文档树样式"""
def print_books_as_tree(userVid=USERVID):
    shelf = get_sorted_bookshelf(userVid)
    #获得{readUpdatetime1:'计算机',...}
    sorted_group = {}
    for group_name in shelf.keys():
        sorted_group[shelf[group_name][0][0]] = group_name
    #排序,得到[(readUpdatetime1,'计算机'),...]
    sorted_group = sorted(sorted_group.items())
    sorted_group.reverse()
    print('\n你的书架')
    #遍历分类
    for group in sorted_group:
        group_name = group[1]
        print('    ┣━━ ' + group_name)
        #遍历分类下的书
        for book in shelf[group_name]:
            book_id = book[1]
            book_name = book[2]
            print('    ┃    ┣━━  ' + book_id + ' '*(9 - len(book_id)) + ' ' + book_name)
        print('    ┃          ')
        print('    ┃          ')
    return ''

def print_chapterUid_and_title(bookId):
    if '_' in bookId:
        print('公众号不支持此命令')
        return ''
    sorted_chapters = get_sorted_chapters(bookId)
    for chapter in sorted_chapters:
        print(str(chapter[0]) + ' '*(5 - len(str(chapter[0]))) + ' ' + chapter[2])

"""按时间返回新内容"""
def get_new_content_bytime(bookId):
    if '_' in bookId:
        print('公众号不支持此命令')
        return ('','')
    #判断temp文件夹是否存在，不存在则创建
    temp_dir = os.getcwd() + "\\temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    """判断createTime文件是否存在"""
    createTime_file = os.getcwd() + "\\temp\\createTime.txt"
    if os.path.isfile(createTime_file):    #如果文件存在
        with open(createTime_file, 'r',encoding='utf-8') as f:
            line = f.readlines()[0]
            synckey = line.split(',')[0][1:]
        #按时间请求最新数据
        url = "https://i.weread.qq.com/book/bookmarklist?" + "bookId=" + bookId + "&synckey=" + synckey
        data = request_data(url)
        if len(data['updated']) == 0:
            print('书中无新标注')
            return ('','')
        else:
            res = get_md_str_from_data(data,is_all_chapter = 0)
            #更新createTime.txt
            with open(createTime_file, 'w',encoding='utf-8') as f:
                time_and_text = {}
                for item in data['updated']:
                    time_and_text[item['createTime']] = item['markText']
                #生成排序后的createTime列表
                sorted_time_and_text = sorted(time_and_text.items())
                #createTime越大，所对应的标注越新
                f.write(str(sorted_time_and_text[-1]))
                print('createTime.txt已更新')
            return (line,res)
    elif not os.path.isfile(createTime_file):   #如果文件不存在
        #获取全部数据
        url = "https://i.weread.qq.com/book/bookmarklist?" + "bookId=" + bookId
        data = request_data(url)
        #生成{createTime:text}字典
        time_and_text = {}
        if len(data['updated']) == 0:
            print('书中无标注')
            return ('','')
        for item in data['updated']:
            time_and_text[item['createTime']] = item['markText']
        #生成排序后的[(createTime:text)]列表
        sorted_time_and_text = sorted(time_and_text.items())
        #创建creaTime.txt文件并写入最新时间
        with open(createTime_file, 'w',encoding='utf-8') as f:
            f.write(str(sorted_time_and_text[-1]))
            print('createTime文件已生成，下次运行函数开始push')
            return ('','')

"""按位置返回新内容"""
def get_new_content_byrange(bookId):
    if '_' in bookId:
        print('公众号不支持此命令')
        return ('','')
    url = "https://i.weread.qq.com/book/bookmarklist?" + "bookId=" + bookId
    #判断temp文件夹是否存在，不存在则创建
    temp_dir = os.getcwd() + "\\temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    #如果range.txt文件存在，获取数据并返回
    if os.path.isfile(temp_dir + "\\range.txt"):
        with open(temp_dir + "\\range.txt", 'r',encoding='utf-8') as f:
            line = f.readlines()[0]
        res = '\n'
        #请求数据
        data = request_data(url)
        if len(data['updated']) == 0:
            print('书中无标注')
            return ('','')
        #获取章节、标注
        sorted_chapters = get_sorted_chapters(bookId)
        sorted_contents = get_sorted_contents_from_data(data)
        #去除没有标注的目录项
        d_sorted_chapters =[]
        for chapter in sorted_chapters:
            if chapter[0] in sorted_contents.keys():
                d_sorted_chapters.append(chapter)
        #获取标注位置(range)及其所在章节id
        line_list = line.replace(' ','').split(',')
        position = (int(line_list[0][1:]),int(line_list[1]))
        #遍历章节
        for chapter in d_sorted_chapters:
            #当章节位于所记录的最新标注所在章节之前
            if chapter[0] < position[1]:
                continue
            #当章节位于所记录的最新标注所在章节
            if chapter[0] == position[1]:
                #遍历章节下的笔记
                for text in sorted_contents[chapter[0]]:
                    #如果标注位置大于所记录的最新位置
                    if text[0] > position[0]:
                        res += set_content_style(text[1],text[2]) + '\n\n'
            #当章节位于所记录的最新标注所在章节之后
            if chapter[0] > position[1]:
                #添加标题
                res += set_chapter_level(chapter[1]) + chapter[2] + '\n\n'
                #遍历章节下的笔记
                for text in sorted_contents[chapter[0]]:
                    res += set_content_style(text[1],text[2]) + '\n\n'
        #未发现新标注则返回
        if res == '\n':
            print('书中无新标注')
            return ('','')
        #发现新标注则更新range.txt并追加新内容到文件
        sorted_chapter_and_contents = sorted(sorted_contents.items())
        last_chapterUid = sorted_chapter_and_contents[-1][0]
        range_and_text = (sorted_contents[last_chapterUid][-1][0],last_chapterUid,sorted_contents[last_chapterUid][-1][2])
        #更新range.txt
        with open(temp_dir + "\\range.txt", 'w',encoding='utf-8') as f:
            f.write(str(range_and_text))
            print('range.txt已更新')
        return (line,res)
    elif not ( os.path.exists(temp_dir + "\\range.txt") or os.path.isfile(temp_dir + "\\range.txt") ):   #如果range.txt文件不存在
        #获取数据
        data = request_data(url)
        #生成{range:text}字典
        if len(data['updated']) == 0:
            print('书中无标注')
            return ('','')
        #获取章节、标注、最新标注所在章节
        sorted_contents = get_sorted_contents_from_data(data)
        sorted_chapter_and_contents = sorted(sorted_contents.items())
        last_chapterUid = sorted_chapter_and_contents[-1][0]
        #储存最新位置的所在位置及章节
        chapterUid_range_and_text = (sorted_contents[last_chapterUid][-1][0],last_chapterUid,sorted_contents[last_chapterUid][-1][2])
        with open(temp_dir + "\\range.txt", 'w+',encoding='utf-8') as f:
            f.write(str(chapterUid_range_and_text))#写入(chapterUid,range,text)
            print('range文件已生成，下次运行函数开始返回新内容')
            return ('','')

def login_success(headers):
    """判断是否登录成功"""
    url = "https://i.weread.qq.com/user/notebooks"
    r = requests.get(url,headers=headers,verify=False)
    if r.ok:
        return True
    else:
        return False