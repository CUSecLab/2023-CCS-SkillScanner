import os
import json

### First generate skill code structure

def get_all_files(root):
    filenames = []
    root_count = root.count('/')
    for path, subdirs, files in os.walk(root):
        if path.count('/') - root_count > 3:
            continue
        if 'module' in path or 'ask_sdk_model' in path: # or 'python' in path:
            continue
        for name in files:
            filenames.append(os.path.join(path, name))
    return filenames


def get_root(path, skill_input_folder):
    if path == skill_input_folder:
        return path
    filenames = get_all_files(path)
    has_code = 0 
    for filename in filenames:
        if filename.endswith('.js') or filename.endswith('.py') or filename.endswith('.java'):
            has_code = 1
            break
    if has_code == 0:
        path = '/'.join(path.split('/')[:-1])
        path = get_root(path, skill_input_folder)
    return path


def get_index(skill_input_folder):
    skills = []
    en_US = []
    for path, subdirs, files in os.walk(skill_input_folder):
        for name in files:
            if name == 'en-US.json':
                en_US.append(path + '/en-US.json')
    if en_US == []:
        print("Don't find a skill")
        return []
    for file in en_US:
        skill = {}
        code_files = []
        manifest_file = ''
        #sub_dir = en_US[0].replace(skill_input_folder,'').split('/')[1]
        #if sub_dir == 'en_US.json':
        #    sub_dir = ''
        #new_skill_input_folder = skill_input_folder + '/' + sub_dir
        #root = get_root(file, new_skill_input_folder)
        root = get_root(file, skill_input_folder)
        filenames = get_all_files(root)
        for filename in filenames:
            if filename.endswith('.js') or filename.endswith('.py'):
                code_files.append(filename)
            if filename.endswith('skill.json'):
                manifest_file = filename
        if len(code_files) > 100:
            continue
        if '(' in root or ')' in root:
            continue
        skill['root'] = root
        skill['intent_file'] = file
        skill['code_files'] = code_files
        skill['manifest_file'] = manifest_file
        skills.append(skill)
    return skills


# Here only write result for each single skill
def write_skill_to_file(skills):
    #x = os.system('mkdir results')
    for skill in skills:
        skill_name = skill['root'].replace('/', '~').replace(' ', '@')
        if os.path.isdir('results/' + skill_name) == False:
            x = os.system('mkdir results/' + skill_name)
            x = os.system('mkdir results/' + skill_name + '/content_safety')
            x = os.system('mkdir results/' + skill_name + '/privacy_violation')
            x = os.system('mkdir results/' + skill_name + '/code_inconsistency')
            x = os.system('mkdir results/' + skill_name + '/taint_analysis')
            x = os.system('mkdir results/' + skill_name + '/htmls')
            x = os.system('mkdir results/' + skill_name + '/mp3')
            x = os.system('mkdir results/' + skill_name + '/image')
        with open('results/' + skill_name  + '/skill.json', 'w') as f:
            x = f.write(json.dumps(skill) + '\n')


def generate_skill_index(skill_input_folder):
    skills = get_index(skill_input_folder)
    write_skill_to_file(skills)
    return skills
