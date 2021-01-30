from requests.models import Response
import tqdm
import requests
import tqdm
headers = {
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
}

tqdm.tqdm.write('come on')

url = 'https://www.zhihu.com/api/v4/questions/{}/answers?include=data[*].content,voteup_count&limit=5&offset=0&sort_by=default'.format('c')

response = requests.get(url=url, headers=headers)

print(response.text)