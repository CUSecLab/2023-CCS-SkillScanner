import git
import csv
import os

def clone_repo(git_url, dst_url):
    print(git_url)
    http_url_head = "https://github.com/"
    tail_url = ".git"
    repo_url = http_url_head + git_url + tail_url
    folder = git_url.split("/")[0]
    item = git_url.split("/")[1]
    if os.path.isdir(dst_url + folder) == False:
        os.mkdir(dst_url + folder)
    if os.path.isdir(dst_url + folder + '/' + item) == False:
        git.Git(dst_url + folder).clone(repo_url)


if __name__ == "__main__":
    links = open("alexa_links.txt").read().split('\n')[:-1]
    links = [link[19:] for link in links]
    dst_url = "repos/"
    count = 0
    for link in links:
        print(count)
        try:
            count = count + 1
            clone_repo(link, dst_url)
        except Exception as error_info:
            print(error_info)
