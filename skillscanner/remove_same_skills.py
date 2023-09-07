import os
import json
from tqdm import tqdm
from copydetect import CopyDetector


def get_files_similarity(skill_folders, file_type):
    code_files = []
    for skill_name in skill_folders:
        try:
            skill = json.loads(open('results/' + skill_name + '/skill.json').read())
        except:
            continue
        if file_type == 'code_files':
            code_files = code_files + skill[file_type]
        else:
            code_files.append(skill[file_type])
    # add files to detector
    # here setting similarity threshold as 0.5, but latter will check again for intent and manifest (1 as threshold)
    detector = CopyDetector(display_t = 0.5, ignore_leaf = True, same_name_only = True)
    for file in code_files:
        if file == '':
            continue
        detector.add_file(file)
    detector.run()
    # get similar files pairs
    results = detector.get_copied_code_list()
    with open('results/' + file_type + '_similarity_0.5.txt', 'w') as f:
        for result in results:
            x = f.write(str(result[0]) + '\t' + str(result[1]) + '\t'  + result[2] + '\t'  + result[3] + '\t'  + str(result[6]) + '\n')


def read_edges(filename):
    results = open(filename).read().split('\n')[:-1]
    edges = {}
    for result in results:
        result = result.split('\t')
        edges[(result[2], result[3])] = (float(result[0]), float(result[1]))
        edges[(result[3], result[2])] = (float(result[1]), float(result[0]))
    return edges


def get_same_skill_pairs(skills, edges_code, edges_intent, edges_manifest):
    same_skill_pairs = []
    for skill1 in tqdm(skills):
        files1 = skill1['code_files']
        for skill2 in skills:
            if skill1 == skill2:
                continue
            files2 = skill2['code_files']
            if len(files1) != len(files2):
                continue
            same_file = 0
            for file1 in files1:
                for file2 in files2:
                    if (file1, file2) not in edges_code:
                        continue
                    if edges_code[(file1, file2)] == (1, 1):
                        same_file = same_file + 1
            if same_file != len(files1):
                continue
            try:
                if edges_intent[(skill1['intent_file'], skill2['intent_file'])] == (1, 1):
                    if edges_manifest[(skill1['manifest_file'], skill2['manifest_file'])] == (1, 1):
                        same_skill_pairs.append((skill1, skill2))
            except:
                continue
    return same_skill_pairs


def group_files(same_skill_pairs):
    group = {}
    for pair in same_skill_pairs:
        m = 0
        skill1, skill2 = pair
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


def get_root_path(skills):
    first_skill = skills[0]['root']
    for i in range(0, len(first_skill)):
        k = 0
        for skill in skills:
            if first_skill[:i] in skill['root']:
                k = k + 1
        if k != len(skills):
            break
    root_path = first_skill[:i - 1]
    return root_path


def get_official_authors(skills, root_path):
    authors = {}
    for skill in skills:
        words = skill['root'].replace(root_path, '').split('/')
        try:
            author = words[0]
            folder = words[1]
        except:
            continue
        if author in authors:
            authors[author].append(folder)
        else:
            authors[author] = [folder]
    official_authors = {}
    for author in authors:
        if len(authors[author]) > 5:
            official_authors[author] = authors[author]
    return official_authors


def get_skill_keep_in_group(group, skills):
    root_path = get_root_path(skills)
    official_authors = get_official_authors(skills, root_path)
    skill_keep_in_group = []
    for i in group:
        for skill in group[i][::-1]:
            if skill['root'].replace(root_path, '').split('/')[0] in official_authors:
                break
        skill_keep_in_group.append(skill)
    return skill_keep_in_group


def remove_same_skills():

    skill_folders = os.listdir('results')

    get_files_similarity(skill_folders, 'code_files')
    get_files_similarity(skill_folders, 'intent_file')
    get_files_similarity(skill_folders, 'manifest_file')

    edges_code = read_edges('results/code_files_similarity_0.5.txt')
    edges_intent = read_edges('results/intent_file_similarity_0.5.txt')
    edges_manifest = read_edges('results/manifest_file_similarity_0.5.txt')

    skills = [json.loads(open('results/' + skill_name + '/skill.json').read()) for skill_name in skill_folders]
    same_skill_pairs = get_same_skill_pairs(skills, edges_code, edges_intent, edges_manifest)
    group = group_files(same_skill_pairs)
    all_skills_in_groups = [item for sublist in group for item in group[sublist]]
    skill_keep_in_group = get_skill_keep_in_group(group, skills)

    print(str(len(all_skills_in_groups) - len(skill_keep_in_group)) + ' skills are same and removed.')
    print(str(len(skills) - len(all_skills_in_groups) + len(skill_keep_in_group)) + ' skills are kept.')

    for skill in skills:
        if skill in skill_keep_in_group:
            continue
        elif skill in all_skills_in_groups:
            x = os.system('rm -r results/' + skill['root'].replace('/', '~').replace(' ', '@'))

