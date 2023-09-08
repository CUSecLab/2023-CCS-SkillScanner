import os
import re
import csv
import json
import time
import spacy
import string
import requests
from tqdm import tqdm

nlp = spacy.load("en_core_web_sm")


# read all the outputs
def read_skill_outputs(skill_name):
    with open('results/' + skill_name + '/content_safety/outputs.csv') as f:
        reader = csv.reader(f)
        outputs = []
        for row in reader:
            outputs.append(row)
    return outputs


def read_media_outputs(skill_name):
    outputs = []
    with open('results/' + skill_name + '/content_safety/outputs_image.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            outputs.append(row)
    with open('results/' + skill_name + '/content_safety/outputs_mp3.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            outputs.append(row)
    #with open('results/outputs_html.csv') as f:
    #    reader = csv.reader(f)
    #    for row in reader:
    #        outputs.append(row[0])
    return outputs


def write_results(filename, outputs):
    with open('results/' + filename, 'w', newline = '') as f: 
        writer = csv.writer(f)
        for output in outputs:
            x = writer.writerow(output)


def get_data_collection_outputs(outputs):
    noun = ['address', 'name', 'email', 'email address', 'birthday', 'age', 'gender', 'location', 'contact', 'phonebook', 'profession', 'income', 'ssn', 'zipcode', 'ethnicity', 'affiliation', 'orientation', 'affiliation', 'postal code', 'zip code', 'first name', 'last name', 'full name', 'phone number', 'social security number', 'passport number', 'driver license', 'bank account number', 'debit card number']
    noun2 = [word.split()[-1] for word in noun]
    add_sentences = {"how old are you": 'age', "when were you born": 'age', "where do you live":'location' ,"where are you from": 'location', "what can i call you": 'name', 'male or female': 'gender', 'what city do you live in?': 'location'}
    words = ['companion app', 'alexa app', 'amazon.com', 'permission', 'enable', 'grant']
    skills = []
    for output in outputs:
        filename, output = output
        output = output.lower()
        if 'you' not in output:
            continue
        if ' ' not in output:
            continue
        sentences = re.split(r' *[\n\,\.!][\'"\)\]]* *', output)
        for sentence in sentences:
            if any (word in output for word in words):
                continue
            if any ('your ' + word + ' is' in sentence for word in noun):
                continue
            if any (word in sentence for word in noun) and 'your' in sentence:
                doc = nlp(sentence)
            for word in noun:
                if word not in sentence or 'your' not in sentence:
                    continue
                if word == 'name' and 'your name' not in sentence:
                    continue
                if word == 'address' and 'email address' in sentence:
                    continue
                if word == 'phone number' and 'dial your local emergency' in sentence:
                    continue
                for l in doc:
                    if l.text == 'your' and l.head.text in noun2 and l.head.text in word:
                        if 'name' in word:
                            skills.append((filename, output, 'collect data name'))
                        else:
                            skills.append((filename, output, 'collect data ' + word))
            for sent in add_sentences:
                    if sent in sentence.translate(str.maketrans('', '', string.punctuation)):
                        skills.append((filename, output, 'collect data ' + add_sentences[sent]))
    return set(skills)


def get_skill_data_collection_in_outputs(skill_name, outputs):
    data_collection_outputs = get_data_collection_outputs(outputs)
    write_results(skill_name + '/content_safety/outputs_data_collection.csv', data_collection_outputs)


# send outputs to perspective and check their toxicity
def get_toxic_request(skill_name, outputs):
    api_key = 'AIzaSyA7p5oAWAHcRsKWcKssRRdd11tqz848H_U'
    url = ('https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze' + '?key=' + api_key)
    if len(outputs) == 0:
        outputs = [['', ' ']]
    for output in tqdm(outputs[:1000]):
        filename, output = output
        data_dict = {'comment': {'text': output},'languages': ['en'],'requestedAttributes': {'TOXICITY': {},'SEVERE_TOXICITY':{},'IDENTITY_ATTACK':{},'INSULT':{},'PROFANITY':{},'THREAT':{}}}
        response = requests.post(url = url, data = json.dumps(data_dict)) 
        response_dict = json.loads(response.content.decode())
        time.sleep(1)
        with open('results/' + skill_name + '/content_safety/toxic_result.txt', 'a') as f:
            x = f.write(filename + '\t' + str(output) + '\t')
            json.dump(response_dict, f)
            x = f.write('\n')


def get_toxic_result(skill_name, outputs):
    results = open('results/' + skill_name + '/content_safety/toxic_result.txt').read().split('\n')[:-1]
    toxic = {}
    for result in results:
        try:
            filename, sentence, response = result.split('\t')
            response_dict = json.loads(response)
            if 'attributeScores' not in response_dict.keys():
                continue
            if response_dict['attributeScores']['PROFANITY']['summaryScore']['value'] < 0.9:
                continue
            if response_dict['attributeScores']['TOXICITY']['summaryScore']['value'] < 0.9:
                continue
            toxic[sentence] = response_dict
        except:
            continue
    results = []
    for output in outputs:
        filename, output = output
        if output in toxic:
            results.append((filename, output))
    return results


def get_toxic_output(skill_name, outputs):
    get_toxic_request(skill_name, outputs)
    toxic_content = get_toxic_result(skill_name, outputs)
    write_results(skill_name + '/content_safety/outputs_toxic.csv', toxic_content)


# a faster version for positive rating (don't check verb)
def get_positive_rating(skill_name, outputs):
    keywords = ['5 star review', 'five star review', '5-star review', '5 star rating', 'five star rating', '5-star rating']
    outputs_with_5_star = []
    for output in outputs:
        filename, output = output
        if any (word in output[1] for word in keywords):
            outputs_with_5_star.append((filename, output))
    write_results(skill_name + '/content_safety/outputs_positive_rating.csv', outputs_with_5_star)


# a complete version that uses nlp to check result
def get_positive_rating(skill_name, outputs):
    keywords = ['5 star review', 'five star review', '5-star review', '5 star rating', 'five star rating', '5-star rating']
    outputs_with_5_star = []
    for output in outputs:
        filename, output = output
        if any (word in output for word in keywords):
            doc = nlp(output)  
            for sentence in doc.sents:
                if any (word in sentence.text for word in keywords):
                    for word in sentence:
                        if word.text == 'star' and (word.head.head.lemma_ == 'leave' or word.head.head.lemma_ == 'give'):
                            outputs_with_5_star.append((filename, output))
    write_results(skill_name + '/content_safety/outputs_positive_rating.csv', outputs_with_5_star)


def get_content_safety(skill_name):
    outputs = read_skill_outputs(skill_name)
    outputs = outputs + read_media_outputs(skill_name)
    # check data collection (prepare for Privacy Violation, pre-6.4.1)
    get_skill_data_collection_in_outputs(skill_name, outputs)
    # check toxic content, asking for positive rating (Content Safety 6.5.1)
    print('---------- Sending outputs to Perspective to scan toxicity ----------')
    get_toxic_output(skill_name, outputs)
    get_positive_rating(skill_name, outputs)



