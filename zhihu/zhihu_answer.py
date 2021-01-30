import requests
import json
from urllib.parse import unquote
import time
import re
import login
from tqdm import tqdm
import utils
from config import config
requests.packages.urllib3.disable_warnings()

def wait_response(url):
    sleep_lengh = 30
    response = None
    while True:
        wait_process_bar = tqdm(total=sleep_lengh, ncols=75)
        wait_process_bar.set_description('等待{}秒'.format(sleep_lengh))
        for i in range(sleep_lengh):
            time.sleep(1)
            wait_process_bar.update(1)
        wait_process_bar.close()
        try:
            response = requests.get(url=url, headers=login.headers, verify=False)
        except Exception as e:
            print('requests Exception：{}'.format(e))
        if response.ok:
            print('获取成功。response.ok：{}'.format(response.ok))
            break
        else:
            print('response.ok：{}'.format(response.ok))
        if sleep_lengh > 60:# 等待时长大于 60 秒时尝试验证或登录
            msg = response.json()
            error = msg['error']
            if not error['need_login'] and error['redirect']:
                print('需要验证。')
                login.main()
            elif error['need_login'] and error['redirect']:
                print('需要登录。')
                login.main()
        sleep_lengh += 30
    return response

""" 分页面获取全部回答，返回一个包含所有分页的 List（每个分页包含若干回答） """
def get_all_answers(question_id):
    if not utils.is_connected():
        print('请求失败，请检查网络。')
        return
    answers = []
    sum = 0
    process_bar = None
    response = None
    url = 'https://www.zhihu.com/api/v4/questions/{}/answers?include=data[*].content,voteup_count&limit=5&offset=0&sort_by=default'.format(question_id)
    while True:
        try:
            response = requests.get(url=url, headers=login.headers, verify=False)
        except Exception as e:# “远程主机强迫关闭了一个现有的连接。”
            print('获取出错：{}'.format(e))
            print(unquote('url：{}'.format(url), encoding='utf-8'))
            response = wait_response(url)
        if not response.ok: # id 不存在或被检测到
            if '404' in response.text:
                print('获取出错：{}。可能输入了错误的问题 id。'.format(response.text))
                break
            print(unquote('url：{}'.format(url), encoding='utf-8'))
            response = wait_response(url)
        json = response.json()
        if json['data']:
            answers.append(json)
            sum += len(json['data'])
            # 进度条
            if len(answers) == 1:
                print('标题：{}'.format(answers[0]['data'][0]['question']['title']))
                process_bar = tqdm(total=answers[0]['paging']['totals'], ncols=75)
                process_bar.set_description("获取")
            process_bar.update(len(json['data']))
            # 检查是否为最后一页
            if not json['paging']['is_end']:
                url = json['paging']['next']
            else:
                break
        else:
            break
    process_bar.close()
    print('获取结束\t总回答数：{}\t获取回答数：{}'.format(answers[0]['paging']['totals'], sum))
    return answers


""" 处理单页数据，返回包含作者、回答内容及点赞数的字符串 """
def get_content(json, config={}):
    res = ''
    answers = json['data']
    count = 0
    for answer in answers:
        count += 1
        author_home_page = ''
        if config['author']:
            author_name = answer['author']['name']
            author_url_token = answer['author']['url_token']
            author_home_page = '[{}]({})'.format(
                author_name, 'https://www.zhihu.com/people/' + author_url_token)
        else:
            author_home_page = '回答 {}'.format(count)
        # 无用 img、figure、noscript 替换为空
        content = re.sub(r'(<img[^>]*src="data[^>]*\/>|<figure>|<noscript>|<\/figure>|<\/noscript>)', '', answer['content'])
        # <br/> 及 <br> 替换为 \n（会影响 HTML，暂时不使用）
        # content = re.sub(r'(<br\/>|<br>)', '\n', content)
        voteup_count = ''
        if config['voteup_count']:
            voteup_count = '**{}**\n\n'.format(answer['voteup_count'])
        res = '{}# {}\n\n{}\n\n{}'.format(res, author_home_page, content, voteup_count)
    return res


""" 将回答写入文件，每个回答页面单独存储在一个文件中 """
def write_to_files(answers, config={}):
    question_dir = ''
    file_names = []
    if answers[0]:
        current_time = time.strftime("%Y-%m-%d %H-%M-%S", time.localtime())
        question_dir = 'temp\\{question_title}\\{current_time}'.format(
            question_title=answers[0]['data'][0]['question']['title'], current_time=current_time)
    else:
        return
    utils.create_dir(question_dir)
    page_count = 0
    # 创建 pages 文件
    print('创建 pages...')
    for page_data in answers:
        page_count += 1
        file_name = 'page{}'.format(page_count)
        # 处理各页的数据之后将其写入文件
        with open(file='.\\{}\\{}.md'.format(question_dir, file_name), mode='w', encoding='utf-8') as file:
            file.write(get_content(page_data, config))
            file_names.append(
                '[{file_name}](./{file_name}.md)'.format(file_name=file_name))
    # 创建各回答的索引文件
    print('创建 index.md...')
    with open(file='.\\{}\\index.md'.format(question_dir,), mode='w', encoding='utf-8') as file:
        for name in file_names:
            file.write(name+'\n\n')
    # 数据保存为 json
    print('创建 answers.json...')
    with open(file='.\\{}\\answers.json'.format(question_dir), mode='w', encoding='utf-8') as file:
        file.write(json.dumps(answers, ensure_ascii=False))
    print('路径：{}'.format(question_dir))


if __name__ == '__main__':
    answers = get_all_answers(268384579)
    write_to_files(answers, config)