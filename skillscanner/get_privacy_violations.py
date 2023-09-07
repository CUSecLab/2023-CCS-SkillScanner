import os
import csv
import json
import spacy
import signal
import subprocess
import trafilatura


def handler(signum, frame):
    print(" ")
    raise Exception(" ")

signal.signal(signal.SIGALRM, handler)

nlp = spacy.load("en_core_web_sm")

### Need to do in this file:
# Read data collection in output, intent and permission, then download and check privacy policy
# Get permission misuse: asked but not used, used but not asked
# Get incorrect disclosure eto Alexa


### read content from manifest file

def get_manifest_content(skill):
    content = {}
    try:
        mainfest = json.loads(open(skill['manifest_file']).read())
    except:
        return {}
    if 'manifest' in mainfest:
        content = mainfest['manifest']
    elif 'skillManifest' in mainfest:
        content = mainfest['skillManifest']
    return content


def get_permission(skill):
    content = get_manifest_content(skill)
    try:
        permissions = content['permissions']
    except:
        permissions = []
    return [permission['name'] for permission in permissions]


def get_privacy_policy_link(skill):
    content = get_manifest_content(skill)
    try:
        privacy_policy = content['privacyAndCompliance']['locales']['en-US']['privacyPolicyUrl']
    except:
        privacy_policy = ""
    return privacy_policy


def get_whether_collect_data_info(skill):
    content = get_manifest_content(skill)
    try:
        collect_data = content['privacyAndCompliance']['usesPersonalInfo']
    except:
        collect_data = ""
    return collect_data


def get_category_name(skill):
    content = get_manifest_content(skill)
    category = open('category_mapping.txt').read().lower().split('\n')[:-1]
    category_mapping = {}
    for i in category:
        developer_category, shown_category = i.split('\t')
        category_mapping[developer_category] = shown_category
    try:
        category = content['publishingInformation']['category'].lower()
        shown_category = category_mapping[category]
    except:
        shown_category = ""
    return shown_category


def get_description(skill):
    content = get_manifest_content(skill)
    try:
        description = content['publishingInformation']['locales']['en-US']['description']
    except:
        description = ""
    return description


### get inconsistency between output, intent and privacy policy

# read all the results
def read_results(filename):
    with open('results/' + filename) as f:
        reader = csv.reader(f)
        results = []
        for row in reader:
            results.append(row)
    return results


# Policylint will keep head content and this library only keeps the main content
def download_privacy_policy(skill_name, privacy_policy_link):
    if privacy_policy_link.endswith('.pdf'):
        x = os.system('curl -L "' + privacy_policy_link + '" >' + 'results/' + skill_name + '/privacy_violation/privacy_policy.pdf')
        x = os.system('pdftotext ' + 'results/' + skill_name + '/privacy_violation/privacy_policy.pdf' + 'privacy_policy.txt > /dev/null 2>&1')
    else:
        try:
            signal.alarm(30)
            command = 'curl -L "' + privacy_policy_link + '" >' + 'results/' + skill_name + '/privacy_violation/privacy_policy.html'
            p = subprocess.Popen(command, universal_newlines = True, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            out, err = p.communicate()
            signal.alarm(0)
            downloaded = trafilatura.load_html(open('results/' + skill_name + '/privacy_violation/privacy_policy.html').read())
            content = trafilatura.extract(downloaded)
            with open('results/' + skill_name + '/privacy_violation/privacy_policy.txt', 'w') as f:
                x = f.write(content)
        except:
            pass


# first check whether have a privacy policy, then download it and check the content
def get_privacy_policy_violation(data_collected, skill, skill_name, data_source):
    not_mention = []
    privacy_policy_link = get_privacy_policy_link(skill)
    with open('results/' + skill_name + '/privacy_violation/privacy_policy_result.txt', 'a') as f:
        if privacy_policy_link == "":
            x = f.write("This skill has data collection " + data_source + " but lacks a privacy policy.\n")
        else:
            try:
                privacy_policy_content = open('results/' + skill_name + '/privacy_violation/privacy_policy.txt').read()
            except:
                x = f.write('This skill has a broken privacy policy.\n')
                privacy_policy_content = ''
            if privacy_policy_content == '':
                x = f.write('This skill has a broken privacy policy.\n')
            for asked_data in data_collected:
                if asked_data not in privacy_policy_content:
                    if asked_data == 'email' and 'e-mail' in privacy_policy_content:
                        continue
                    not_mention.append(asked_data)
            if not_mention != []:
                x = f.write("This skill has an incomplete privacy policy: data " + str(not_mention) + " collected in " + data_source + " is not mentioned in privacy policy.\n")


# read collected data and check whether privacy policy is complete
def get_data_collection_in_output(skill_name, skill):
    output_data_collection = read_results(skill_name + '/content_safety/outputs_data_collection.csv')
    data_collected_in_output = []
    for output in output_data_collection:
        filename, output, data_type = output
        data_collected_in_output.append(data_type[13:])
    with open('results/' + skill_name + '/privacy_violation/privacy_policy_result.txt', 'w') as f:
        x = f.write("")
    if len(data_collected_in_output) > 0:
        get_privacy_policy_violation(data_collected_in_output, skill, skill_name, 'output')
    return data_collected_in_output
    

def get_data_collection_in_intent(skill_name, skill):
    data_collection_intents = read_results(skill_name + '/code_inconsistency/intent_output.csv') + read_results(skill_name + '/code_inconsistency/intent_no_output.csv')
    data_collected_in_intents = [intent[-1] for intent in data_collection_intents]
    #if len(data_collected_in_intents) > 0:
    #    get_privacy_policy_violation(data_collected_in_intents, skill, skill_name, 'intent')
    return data_collected_in_intents


def get_data_collection_in_permission(skill_name, skill):
    permission_mapping = {}
    permission_mapping['alexa::devices:all:address:full:read'] = 'address'
    permission_mapping['alexa:devices:all:address:country_and_postal_code:read'] = 'postal code'
    permission_mapping['alexa::profile:name:read'] = 'name'
    permission_mapping['alexa::profile:given_name:read'] = 'name'
    permission_mapping['alexa::profile:email:read'] = 'email'
    permission_mapping['alexa::profile:mobile_number:read'] = 'number'
    permission_mapping['alexa::devices:all:geolocation:read'] = 'location'
    permission_asked = get_permission(skill)
    data_collected_in_permission = []
    for permission in permission_asked:
        if permission in permission_mapping:
            data_collected_in_permission.append(('skills.json', permission_mapping[permission]))
    write_results(skill_name + '/privacy_violation/permissions.csv', data_collected_in_permission)
    if len(data_collected_in_permission) > 0:
        get_privacy_policy_violation([permission[1] for permission in data_collected_in_permission], skill, skill_name, 'permission')
    return [permission[1] for permission in data_collected_in_permission]


def write_results(filename, outputs):
    with open('results/' + filename, 'a', newline = '') as f: 
        writer = csv.writer(f)
        for output in outputs:
            x = writer.writerow(output)


# same with 2_get_content_safety.py
# a faster version for positive rating (don't check verb)
def get_positive_rating(skill_name, description):
    keywords = ['5 star review', 'five star review', '5-star review', '5 star rating', 'five star rating', '5-star rating']
    if any (word in description for word in keywords):
        outputs_with_5_star = ("", description)
    else:
        outputs_with_5_star = []
    write_results(skill_name + '/content_safety/outputs_positive_rating.csv', outputs_with_5_star)


# found 13 skills in Health category without disclaimer
def check_description(skill_name, skill):
    description = get_description(skill).lower()
    get_positive_rating(skill_name, description)
    category = get_category_name(skill)
    has_disclaimer = 0
    with open('results/' + skill_name + '/content_safety/health_lack_disclaimer.txt', 'w') as f:
        if 'health' not in category:
            return None
        disclamier = 'This tool does not provide medical advice, and is for informational and educational purposes only, and is not a substitute for professional medical advice.'
        doc_dis = nlp(disclamier)
        if 'medical advice' in description or 'educational purpose' in description or 'informational purpose' in description:
            has_disclaimer = 1
            return None
        doc = nlp(description)
        for sentence in doc.sents:
            if doc_dis.similarity(sentence) > 0.93:
                has_disclaimer = 1
        if has_disclaimer == 0:
            x = f.write(str("This skill is in Health category but lacks a disclaimer"))


# found 1 in kids with data collection 
def get_category_issue(skill_name, skill, data_collected):
    with open('results/' + skill_name + '/content_safety/category_data_collection.txt', 'w') as f:
        if len(data_collected) == 0:
            return None
        category = get_category_name(skill)
        if 'health' in category.lower():
            x = f.write('This skill collects data in health category.\n')
        if 'kids' in category.lower():
            x = f.write('This skill collects data in kids category.\n')


def get_permission_overprivilege(skill_name, skill):
    permission_used_type1 = ['/v1/devices/', '/v2/accounts/', '/v2/persons/', 'context.Geolocation']
    permission_used_type2 = ['serviceClientFactory.getDeviceAddressServiceClient()', 'serviceClientFactory.getUpsServiceClient()', 
                            'service_client_factory.get_ups_service', 'service_client_factory.get_device_address_service']
    permission_mapping = {}
    permission_mapping['alexa::devices:all:address:full:read'] = 'FullAddress'
    permission_mapping['alexa:devices:all:address:country_and_postal_code:read'] = 'CountryAndPostalCode'
    permission_mapping['alexa::profile:name:read'] = 'ProfileName'
    permission_mapping['alexa::profile:given_name:read'] = 'ProfileGivenName'
    permission_mapping['alexa::profile:email:read'] = 'ProfileEmail'
    permission_mapping['alexa::profile:mobile_number:read'] = 'ProfileMobileNumber'
    permission_mapping['alexa::devices:all:geolocation:read'] = 'context.geolocation'
    permission_mapping['alexa::devices:all:geolocation:read'] = 'context.Geolocation'
    permission_used_type3 = permission_mapping.values()
    permission = get_permission(skill)
    permission_asked = []
    for permission in permission:
        if permission in permission_mapping:
            permission_asked.append(permission)
    permission_used = []
    for file in skill['code_files']:
        try:
            content = open(file).read().split('\n')[:-1]
        except:
            continue
        for line in range(0, len(content)):
            if len(content[line]) > 1000:
                continue
            if any (word in content[line] for word in permission_used_type1):
                permission_used.append((file, content[line]))
            if any (word in content[line] for word in permission_used_type2):
                permission_used.append((file, content[line]))
            if any (word in content[line] for word in permission_used_type3):
                permission_used.append((file, content[line]))
    not_ask_but_use = set(permission_used) - set(permission_asked)
    # This is only part of ask but not used permissions because permission might be called in code but not used
    ask_but_not_use = set(permission_asked) - set(permission_used)
    with open('results/' + skill_name + '/privacy_violation/permission_usage.txt', 'a') as f:
        x = f.write("permission used but not asked: " + str(not_ask_but_use) + '\n')
        x = f.write("permission asked but not used: " + str(ask_but_not_use) + '\n')


def get_whether_collect_data(skill_name, skill, data_collected):
    whether_collect_data = get_whether_collect_data_info(skill)
    with open('results/' + skill_name + '/privacy_violation/disclosure_to_alexa.txt', 'w') as f:
        if len(data_collected) > 0 and whether_collect_data == False:
            x = f.write("False disclosure to Alexa")


def get_privacy_violations(skill_name):

    skill = json.loads(open('results/' + skill_name + '/skill.json').read())

    privacy_policy_link = get_privacy_policy_link(skill)
    download_privacy_policy(skill_name, privacy_policy_link)

    # 6.4.1
    data_collected_in_output = get_data_collection_in_output(skill_name, skill)
    data_collected_in_intent = get_data_collection_in_intent(skill_name, skill)
    data_collected_in_permission = get_data_collection_in_permission(skill_name, skill)

    # They are part of content safety (6.5.3)
    check_description(skill_name, skill)
    get_category_issue(skill_name, skill, data_collected_in_output + data_collected_in_intent + data_collected_in_permission)

    # 6.4.2
    get_permission_overprivilege(skill_name, skill)

    # 6.4.3
    get_whether_collect_data(skill_name, skill, data_collected_in_output + data_collected_in_intent + data_collected_in_permission)
