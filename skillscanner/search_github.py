from github import Github
import time

ACCESS_TOKEN = open('tokens.txt').read().split('\n')[0][13:]
g = Github(ACCESS_TOKEN)
print(g.get_user().get_repos())

rate_limit = g.get_rate_limit()
rate = rate_limit.search
rate

intents = "interactionModel languageModel invocationName types intents"

publishing = "manifest publishingInformation locales en-US examplePhrases"

step = 1024
start = 0
end = start + step

def search_github_skills():
    for i in range(0,100):
        try:
            query = 'interactionModel languageModel invocationName intents size:' + str(start) + '..' + str(end) +' filename:en-US.json language:JSON'
            result = g.search_code(query, order='desc')
            count = result.totalCount
        except:
            print("first part limit")
            time.sleep(60)
            continue
        print(start, end, count)
        if count == 1000:
            step = int(step/2)
            end = start + step
            time.sleep(2)
        else:
            with open('alexa_links.txt', 'a') as f:
                for j in result:
                    try:
                        x = f.write(j.repository.html_url + '\n')
                        time.sleep(2)
                    except:
                        print("second part limit")
                        time.sleep(60)
                        x = f.write(j.repository.html_url + '\n')
                        continue
            start = end
            end = start + step



def search_github(keyword):
    
    if rate.remaining == 0:
        print(f'You have 0/{rate.limit} API calls remaining. Reset time: {rate.reset}')
        return
    else:
        print(f'You have {rate.remaining}/{rate.limit} API calls remaining')
    query = f'"{keyword} english" in:file extension:po'
    result = g.search_code(query, order='desc')
    max_size = 100
    print(f'Found {result.totalCount} file(s)')
    if result.totalCount > max_size:
        result = result[:max_size]
    for file in result:
        print(f'{file.download_url}')


if __name__ == '__main__':
    keyword = input('Enter keyword[e.g french, german etc]: ')
    search_github_skills()
    #search_github(keyword)


import validators
 
from svn.remote import RemoteClient
 
def download_folder(url):
    if 'tree/master' in url:
        url = url.replace('tree/master', 'trunk')
 
    r = RemoteClient(url)
    r.export('output')
    
 
if __name__ == '__main__':
    url = input('Enter folder url: ')
    if not validators.url(url):
        print('Invalid url')
    else:
        download_folder(url)

