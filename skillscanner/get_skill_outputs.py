import os
import re
import csv
import json
import signal
import requests
import subprocess
from bs4 import BeautifulSoup


def handler(signum, frame):
    #print(" ")
    raise Exception(" ")

signal.signal(signal.SIGALRM, handler)


def remove_comments(lines):
    commented = 0
    new_lines = []
    for line in lines:
        line = line.strip()
        if line == '':
            continue
        if line[0] == '#' or line[:2] == '//':
            continue
        if line[:3] == '\'\'\'' or line[:3] == '"""' or line[:2] == '/*':
            commented = 1
        if line[-3:] == '\'\'\'' or line[-3:] == '"""' or line[-2:] == '*/':
            commented = 0
            continue
        if commented == 1:
            continue
        new_lines.append(line)
    return new_lines


def get_lines_outputs(lines):
    outputs = []
    for line in lines:
        outputs = outputs + re.findall('\'([^\']*)\'', line.replace('\'s', ' is'))
        outputs = outputs + re.findall('"([^"]*)"', line)
        outputs = outputs + re.findall('`([^`]*)`', line)
    outputs = list(set(outputs))
    return outputs


def get_file_outputs(filename):
    try:
        lines = open(filename).read().split('\n')[:-1]
    except:
        return []
    lines = remove_comments(lines)
    outputs = get_lines_outputs(lines)
    outputs = [(filename, output) for output in outputs]
    outputs_with_sentence_or_website = []
    for output in outputs:
        filename, output = output
        if len(output) > 500:
            continue
        if ' ' in output or 'http' in output:
            outputs_with_sentence_or_website.append((filename, output))
    return outputs_with_sentence_or_website


def get_file_response(filename):
    try:
        lines = open(filename).read().split('\n')[:-1]
    except:
        return []
    names = ['.speak(', '.ask(', '.reprompt(', 'this.emit(\':tell\', ', 'this.emit(\':ask\', ']
    responses = []
    for i in range(0, len(lines)):
        for name in names:
            content = lines[i]
            while True:
                start = content.find(name)
                if start == -1:
                    break
                code1 = content[start + len(name):]
                end = code1.find(')')
                responses.append((filename, code1[:end], i + 1, start + len(name) + 1, i + 1, start + len(name) + end))
                code2 = code1[end:]
                content = code2
    return responses


def write_results(filename, outputs):
    with open('results/' + filename, 'w', newline = '') as f: 
        writer = csv.writer(f)
        for output in outputs:
            x = writer.writerow(output)


# get all skill outputs string from code (also need to wait for later website and media outputs)
def get_skill_outputs(skill):
    outputs = []
    responses = []
    for file in skill['code_files']:
        outputs = outputs + get_file_outputs(file)
        responses = responses + get_file_response(file)
    skill_name = skill['root'].replace('/', '~').replace(' ', '@')
    write_results(skill_name + '/content_safety/outputs.csv', outputs)
    write_results(skill_name + '/content_safety/response.csv', responses)


# read all the outputs
def read_skill_outputs(skill_name):
    with open('results/' + skill_name + '/content_safety/outputs.csv') as f:
        reader = csv.reader(f)
        outputs = []
        for row in reader:
            outputs.append(row)
    return outputs


def get_websites(outputs):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    websites = []
    for output in outputs:
        try:
            signal.alarm(1)
            filename, output = output
            url = re.findall(regex, output)
            for i in url:
                websites.append((filename, i[0]))
            signal.alarm(0)
        except:
            continue
    return websites


def separate_websites(websites):
    mp3 = []
    image = []
    html = []
    for website in websites:
        filename, website = website
        if website[-1] == '/':
            website = website[:-1]
        if website[-1] == '\'':
            website = website[:-1]
        if website[-1] == '"':
            website = website[:-1]    
        last = website.split('/')[-1]
        if '?' in last:
            suffix = last.split('?')[-2].split('.')[-1]
        else:
            suffix = last.split('.')[-1]
        if suffix == 'mp3' or suffix == 'mp3"':
            mp3.append((filename, website))
        elif suffix == 'jpg' or suffix == 'png':
            image.append((filename, website))
        else:
            html.append((filename, website))
    return mp3, image, html


## check whether htmls are malicious
## 500 rquests/day
def get_malicious_html(html):
    malicious_htmls = []
    for link in html:
        try:
            filename, link = link
            url = 'https://www.virustotal.com/vtapi/v2/url/scan'
            params = {'apikey': '43ec2a3e2d928f1424cf38d4e05ef8627842eb2a0bd1eacc333d7f6f3f9f8265', 'url': link}
            response = requests.post(url, data = params)
            id = response.json()['scan_id']
            url = 'https://www.virustotal.com/vtapi/v2/url/report'
            params = {'apikey': '43ec2a3e2d928f1424cf38d4e05ef8627842eb2a0bd1eacc333d7f6f3f9f8265', 'resource': id}
            response = requests.get(url, params = params)
            if response.json()['positives'] > 0:
                malicious_htmls.append((filename, link))
        except:
            continue
    return malicious_htmls


def download_html(skill_name, html):
    for link in html:
        filename, link = link
        try:
            signal.alarm(10)
            command = 'curl -L "' + link + '" > ' + 'results/' + skill_name + '/htmls/' + link.replace('/', '~')
            p = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = p.communicate()
            signal.alarm(0)
        except:
            continue


def get_html_content(skill_name):
    outputs = []
    files = os.listdir('results/' + skill_name + '/htmls/')
    for file in files:
        try:
            content = open('results/' + skill_name + '/htmls/' + file).read()
        except:
            continue
        soup = BeautifulSoup(content, features = "html.parser")
        text = soup.get_text()
        sentences = re.split(r' *[\n\,\.!][\'"\)\]]* *', text)
        for sen in sentences:
            if ' ' not in sen:
                continue
            outputs.append((file.replace('~', '/'), sen))
    return outputs


#apt install tesseract-ocr libtesseract-dev libleptonica-dev pkg-config
#pip install python-dateutil
#pip install pillow pytesseract 

from PIL import Image
import pytesseract

def download_image_files(skill_name, image):
    for link in image:
        filename, link = link
        try:
            signal.alarm(10)
            #cmd = ['wget', '-O', 'results/' + skill_name + '/image/' + link.replace('/', '~'), link]
            #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            command = 'wget -O ' + 'results/' + skill_name + '/image/' + link.replace('/', '~') + ' ' + link
            p = subprocess.Popen(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = p.communicate()
            signal.alarm(0)
        except:
            continue


def read_image_files(skill_name):
    filenames = os.listdir('results/' + skill_name + '/image')
    image_outputs = []
    for filename in filenames:
        try:
            content = pytesseract.image_to_string(Image.open('results/' + skill_name + '/image/' + filename)).strip()
        except:
            continue
        if content != '':
            image_outputs.append((filename.replace('~', '/'), content))
    return image_outputs


# pip install ffmpeg
# pip install pydub
# pip install SpeechRecognition
from pydub import AudioSegment
import speech_recognition as sr

def download_mp3_files(skill_name, mp3):
    for link in mp3:
        filename, link = link
        try:
            signal.alarm(10)
            #cmd = ['wget', '-O', 'results/' + skill_name + '/image/' + link.replace('/', '~'), link]
            #p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            command = 'wget -O ' + 'results/' + skill_name + '/mp3/' + link.replace('/', '~') + ' link'
            p = subprocess.Popen(command, universal_newlines = True, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            out, err = p.communicate()
            signal.alarm(0)
        except:
            continue

def read_mp3_files(skill_name):
    filenames = os.listdir('results/' + skill_name + '/mp3')
    mp3_outputs = []
    for filename in filenames:
        try:
            sound = AudioSegment.from_mp3('results/' + skill_name + '/mp3/' + filename)
            x = sound.export('results/' + skill_name + '/mp3/' + filename[:-4] + '.wav', format="wav")
            r = sr.Recognizer()
            with sr.AudioFile('results/' + skill_name + '/mp3/' + filename[:-4] + '.wav') as source:
                audio = r.record(source)
            try:
                s = r.recognize_google(audio)
                mp3_outputs.append((filename.replace('~', '/'), s))
            except Exception as e:
                continue
        except:
            continue
    return mp3_outputs


def check_htmls(skill_name, html):
    # first check if any malicious websites
    malicious_htmls = get_malicious_html(html)
    write_results(skill_name + '/content_safety/malicious_html.csv', malicious_htmls)
    # second download all websites and check websites content
    download_html(skill_name, html)
    html_outputs = get_html_content(skill_name)
    write_results(skill_name + '/content_safety/outputs_html.csv', html_outputs)


def check_mp3(skill_name, mp3):
    download_mp3_files(skill_name, mp3)      # no data collection violation
    mp3_outputs = read_mp3_files(skill_name)
    write_results(skill_name + '/content_safety/outputs_mp3.csv', mp3_outputs)


def check_image(skill_name, image):
    download_image_files(skill_name, image)
    image_outputs = read_image_files(skill_name)
    write_results(skill_name + '/content_safety/outputs_image.csv', image_outputs)


def get_all_outputs(skill_name):
    skill = json.loads(open('results/' + skill_name + '/skill.json').read())
    get_skill_outputs(skill)
    outputs = read_skill_outputs(skill_name)
    websites = get_websites(outputs)
    mp3, image, html = separate_websites(websites)
    # first check websites
    check_htmls(skill_name, html[:10])
    # second check medias
    check_mp3(skill_name, mp3[:10])
    check_image(skill_name, image[:10])



