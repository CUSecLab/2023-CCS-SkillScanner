import os


### get skill group of each violation

def read_all_results():
    results = {}
    with open('all_results_new.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[2] == '':
                continue
            if row[0] != '':
                violation_type = row[0]
                results[violation_type] = []
            results[violation_type].append(row[2])
    return results


# get output data collection
def get_code_file(problematic_skills):
    outputs = []
    f = open('result/output_data_collection.csv')
    reader = csv.reader(f)
    for row in reader:
        outputs.append(row)
    outputs = [(i[0], i[1], i[2], '/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/' + i[3]) for i in outputs]
    outputs2 = []
    for i in outputs:
        if i[0] in problematic_skills:
            outputs2.append(i)
    similar_files = []
    for i in outputs2:
        for j in outputs2:
            if i[0] == j[0]:
                continue
            if i[1:3] == j[1:3]:
                try:
                    if (i[3], j[3]) in edges_code:  ## set threshold here. in edges means threshold is 0.5
                        similar_files.append((i,j))
                except:
                    continue
    return similar_files


def get_similar_files(files, file_type):
    if file_type == 'intent_file':
        edges = edges_intent
    if file_type == 'manifest_file':
        edges = edges_manifest
    similar_files = []
    for i in files:
        for j in files:
            if i == j:
                continue
            try:
                if edges[(i, j)] == (1, 1):         ## set threshold here. (1,1) means two files are same
                    similar_files.append((i, j))
            except:
                continue
    return similar_files


# get intent file
def get_front_end_or_manifest(problematic_skills, file_type):
    problematic_skills = [i.replace('~', '/') for i in problematic_skills]
    files = []
    for problem_skill in problematic_skills:
        for skill in skills:
            if problem_skill in skill['root']:
                files.append(skill[file_type])
    similar_files = get_similar_files(files, file_type)
    return similar_files


def group_files(similar_files):
    group = {}
    for i in similar_files:
        m = 0
        skill1, skill2 = i
        for k in group:
            if skill1 in group[k]:
                m = 1
                if skill2 not in group[k]:
                    group[k].append(skill2)
                break
            if skill2 in group[k]:
                m = 1
                if skill1 not in group[k]:
                    group[k].append(skill1)
                break
        if m == 0:
            k = len(group)
            group[k] = []
            group[k].append(skill1)
            group[k].append(skill2)
    return group


def main():
#    prepare_similarity()

problematic_skills_with_types = read_all_results()

types = {}
types['code'] = ['output incomplete privacy policy', 'output lack a privacy policy', 'output no intent']
types['intent'] = ['invocation name', 'intent no output', 'slot no sample', 'intent no sample']
types['manifest'] = ['permission lack a privacy policy', 'disclosure lack a privacy policy',
'permission incomplete privacy policy', 'disclosure incomplete privacy policy', 'permission not used', 'disclosure']

# show how many skills caused by copy
for type in problematic_skills_with_types:
    if type in types['code']:
        similar_files = get_code_file(problematic_skills_with_types[type])
    elif type in types['intent']:
        similar_files = get_front_end_or_manifest(problematic_skills_with_types[type], 'intent_file')
    elif type in types['manifest']:
        similar_files = get_front_end_or_manifest(problematic_skills_with_types[type], 'manifest_file')
    else:
        continue
    group = group_files(similar_files)
    sorted_group = sorted(group, key = lambda k: len(group[k]), reverse = True)
    skills_copied_and_source = [item for sublist in group for item in group[sublist]]
    if type in types['code']:
        top_author = get_top_author_of_group_output(group)
        skills_copied_and_source = [i[0] for i in skills_copied_and_source]
        skills_source = get_top_author_output(group)
        print(type, len(problematic_skills_with_types[type]), len(set(skills_copied_and_source)), len(group) - sum([i[1] for i in skills_source]) + len(skills_source), len(group[sorted_group[0]]), top_author[sorted_group[0]])
    else:
        try:
            top_author = get_top_author_of_group(group)
            print(type, len(problematic_skills_with_types[type]), len(set(skills_copied_and_source)), len(group), len(group[sorted_group[0]]), top_author[sorted_group[0]])
        except:
            print(type, len(problematic_skills_with_types[type]), len(set(skills_copied_and_source)), len(group), len(group[sorted_group[0]]))




if __name__ == "__main__":
    main()




def get_official_authors():
    authors = {}
    for skill in skills:
        words = skill['root'].split('/')
        author = words[12]
        folder = words[13]
        if author in authors:
            authors[author].append(folder)
        else:
            authors[author] = [folder]
    official_authors = {}
    for author in authors:
        if len(authors[author]) > 5:
            official_authors[author] = authors[author]
    return official_authors


def get_top_author_of_group_output(group):
    official_authors = get_official_authors()
    first_author_of_group = []
    for i in group:
        authors_of_group = {}
        for author in set([k[0].split('~')[1] for k in group[i]]):
            if author in official_authors:
                authors_of_group[author] = official_authors[author]
        if authors_of_group == {}:
            first_author_of_group.append('')
            continue
        sorted_authors_of_group = sorted(authors_of_group, key = lambda k: len(authors_of_group[k]), reverse = True)
        first_author_of_group.append(sorted_authors_of_group[0])
    return first_author_of_group


def get_top_author_of_group(group):
    official_authors = get_official_authors()
    first_author_of_group = []
    for i in group:
        author_of_group_folders = {}
        for author in set([k.split('/')[12] for k in group[i]]):
            if author in official_authors:
                author_of_group_folders[author] = official_authors[author]
        if author_of_group_folders == {}:
            first_author_of_group.append('')
            continue
        sorted_author_of_group = sorted(author_of_group_folders, key = lambda k: len(author_of_group_folders[k]), reverse = True)
        first_author_of_group.append(sorted_author_of_group[0])
    return first_author_of_group


def get_top_author_output(group):
    official_authors = get_official_authors()
    first_author_of_group = {}
    for i in group:
        author_of_group_folders = {}
        for author in set([k[0].split('~')[1] for k in group[i]]):
            if author in official_authors:
                author_of_group_folders[author] = official_authors[author]
        if author_of_group_folders == {}:
            continue
        sorted_author_of_group = sorted(author_of_group_folders, key = lambda k: len(author_of_group_folders[k]), reverse = True)
        try:
            first_author_of_group[sorted_author_of_group[0]] = first_author_of_group[sorted_author_of_group[0]] + 1
        except:
            first_author_of_group[sorted_author_of_group[0]] = 1
    sorted_author = sorted(first_author_of_group.items(), key=lambda kv: kv[1], reverse = True)
    return sorted_author



# find which author (alexa) is always copied

problematic_skills_with_types = read_all_results()
#problematic_skills_with_types = problematic_skills_with_types_after
for type in problematic_skills_with_types:
    break

similar_files = get_code_file(problematic_skills_with_types[type])
group = group_files(similar_files)
# group = group_files(same_skills)
# skills_in_groups = [item['root'] for sublist in group for item in group[sublist]]
# not_copied_skills_in_groups = [group[i][0]['root'] for i in group]

# all skills (copy source + copied skills)
skills_in_groups = [item['root'] for sublist in group for item in group[sublist]]

# copy source skills
not_copied_skills_in_groups = [group[i][0]['root'] for i in group]

problematic_skills_with_types_before = read_all_results()
problematic_skills_with_types_after = read_all_results()

violations_in_copied_skills = []
for i in problematic_skills_with_types_before:
    for j in problematic_skills_with_types_before[i]:
        if '/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/' + j.replace('~', '/') not in not_copied_skills_in_groups:
            if '/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/' + j.replace('~', '/') in skills_in_groups:
                violations_in_copied_skills.append(j)

len(violations_in_copied_skills), len(set(violations_in_copied_skills))

for i in problematic_skills_with_types_before:
    for j in problematic_skills_with_types_before[i]:
        if '/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/' + j.replace('~', '/') not in not_copied_skills_in_groups:
            if '/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/' + j.replace('~', '/') in skills_in_groups:
                problematic_skills_with_types_after[i].remove(j)



for i in problematic_skills_with_types_after:
    print(i, len(set(problematic_skills_with_types_before[i])))
    print(i, len(set(problematic_skills_with_types_after[i])))

sum([len(problematic_skills_with_types_after[i]) for i in problematic_skills_with_types_after])


with open('all_results.json', 'w') as f:
    x = f.write(json.dumps(problematic_skills_with_types_after))



# check alexa-samples code privacy policy

from pathlib import Path

def get_file_list(dirs, exts):
    file_list = []
    for dir in dirs:
        for ext in exts:
            if ext == "*":
                matched_contents = Path(dir).rglob("*")
            else:
                matched_contents = Path(dir).rglob("*." + ext.lstrip("."))
            files = [str(f) for f in matched_contents if f.is_file()]
            file_list.extend(files)
    return list(set(file_list))


# check whether privacy policy need
need_policy = {}
for author in amazon_authors:
    need_policy[author] = []
    for type in problematic_skills_with_types:
        if 'privacy policy' in type:
            for skill in problematic_skills_with_types_after[type]:
                if skill.split('~')[1] == author:
                    need_policy[author].append(skill)


for author in need_policy:
    print(author, len(set(need_policy[author])))


# check whether privacy policy provided
for author in need_policy:
    with_policy = 0
    for skill in set(need_policy[author]):
        manifest_file = ''
        for skill2 in skills:
            if skill2['root'] == '/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/' + skill.replace('~','/'):
                try:
                    manifest_file = skill2['manifest_file']
                except:
                    print(skill, 'lack manifest file')
                    continue
        if manifest_file == '':
            continue
        a = open(manifest_file).read()
        if 'privacyPolicyUrl' in a:
            with_policy = with_policy + 1
        else:
            print(skill)
    print(author, with_policy, len(set(need_policy[author])))





# check whether invocation name has problems (19 skills)
invocation_names = open('result/invocation_name.txt').read().split('\n')[:-1]
for author in amazon_authors:
    files = get_file_list(['repos/' + author], ['.json'])
    intent_file = 0
    with_policy = 0
    for file in files:
        if file.endswith('en-US.json'):
            intent_file = intent_file + 1
            a = open(file).read().split('\n')[:-1]
            for j in a:
                if 'invocationName' in j:
                    for word in invocation_names:
                        if '"' + word + '"' in j:
                            print(author + '`' +  file + '`' + j + '`' + word)


# check how many official violations

test = []
for type in problematic_skills_with_types:
    # 25 skills
    if 'output lack a privacy policy' not in type and 'permission lack a privacy policy' not in type and 'invocation name' not in type:
        continue
    for author in amazon_authors:
        for skill in problematic_skills_with_types[type]:
            if skill.split('~')[1] == author:
                print(type, skill)
                test.append(skill)
    print(type, len(test))




# show how many skills caused by copying official skills

amazon_authors = ['alexa', 'alexa-dev-hub', 'alexa-labs', 'alexa-samples', 'aws-samples']

copied_skills = {}

for author in tqdm(amazon_authors):
    copied_skills[author] = []
    for type in problematic_skills_with_types:
        if 'output lack a privacy policy' not in type and 'permission lack a privacy policy' not in type and 'invocation name' not in type:
            continue
        if type in types['code']:
            similar_files = get_code_file(problematic_skills_with_types[type])
        elif type in types['intent']:
            similar_files = get_front_end_or_manifest(problematic_skills_with_types[type], 'intent_file')
        elif type in types['manifest']:
            similar_files = get_front_end_or_manifest(problematic_skills_with_types[type], 'manifest_file')
        else:
            continue
        group = group_files(similar_files)
        if type in types['code']:
            for i in group:
                for j in group[i]:
                    if author == j[0].split('~')[1]:
                        for k in group[i]:
                            if k[0].split('~')[1] in amazon_authors:
                                continue
                            copied_skills[author].append((type, j[0].replace('repos~','').replace('~','/'), k[0].replace('repos~','').replace('~','/')))
                        break
        else:
            for i in group:
                for j in group[i]:
                    if author == j.split('/')[12]:
                        for k in group[i]:
                            if k.split('/')[12] in amazon_authors:
                                continue
                            copied_skills[author].append((type, j.replace('/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/repos/', ''), k.replace('/home/liao5/../../zfs/socbd/liao5/real-time-tweet/tweepy/icse/repos/', '')))
                        break



sorted_authors = sorted(copied_skills, key = lambda k: len(copied_skills[k]), reverse = True)

for author in sorted_authors:
    print(author, len(set([i[2] for i in copied_skills[author]])))

for author in copied_skills:
    for i in copied_skills[author]:
        print(author + '`' +  i[0] + '`' + i[1] + '`' + i[2])




'''

output privacy policy
permission privacy policy
invocation name


lack:
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~03
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~04
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~05
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~05_intent_chaining
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~06
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~07
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~08
repos~alexa-samples~skill-sample-nodejs-zero-to-hero~09


have
alexa-samples/skill-sample-nodejs-zero-to-hero/10/skill-package/skill.json
alexa-samples/skill-sample-nodejs-cloudformation-guide/06_apiGatewaySkill/skill-package/skill.json
alexa-samples/amazon-pay-demo/skill.json
alexa-samples/alexa-salesforce-notes-sample/skill.json
alexa-samples/alexa-heroku-sales-assistant-sample/alexa-skill-assets/skill.json
alexa-samples/error-notification-sample-skill/skill-package/skill.json
alexa-samples/timers-demo/skill-package/skill.json
'''