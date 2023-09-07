import os
import sys
import json
import time
from tqdm import tqdm

import generate_skill_index
import remove_same_skills
import get_skill_outputs
import get_content_safety
import get_code_inconsistency
import get_privacy_violations
import run_codeql
import get_dataset_statistic
import generate_report


def check_skill(root_path, folder):
    time0 = time.time()
    print('\nFinding skills...\n')
    try:
        skills = generate_skill_index.generate_skill_index(root_path + '/' + folder)
    except:
        return None
    if skills == []:
        return None
    #remove_same_skills.remove_same_skills()
    intent_number, slot_number, sample_number, function_number = get_dataset_statistic.get_dataset_statistic(skills)
    time1 = time.time()
    print('Found ' + str(len(skills)) + ' skills, each skill costs ' + str((time1 - time0)/len(skills)) + ' s on average.\n')
    for skill in skills:
        skill_name = skill['root'].replace('/', '~').replace(' ', '@')
        if os.path.isfile('results/' + skill_name + '/report.txt'):
            continue
        print(skill_name)
        time2 = time.time()
        print('---------- Scanning skill output and content safety ----------\n')
        get_skill_outputs.get_all_outputs(skill_name)
        get_content_safety.get_content_safety(skill_name)
        get_code_inconsistency.get_skill_invocation_name_issue(skill_name, skill)
        time3 = time.time()
        print('---------- Scanning skill code inconsistency ----------\n')
        get_code_inconsistency.get_code_inconsistency(skill_name, skill)
        time4 = time.time()
        get_privacy_violations.get_privacy_violations(skill_name)
        time5 = time.time()
        run_codeql.run_codeql(skill_name)
        time6 = time.time()
        print('Scanning one skill cost ' + str(time6 - time2) + ' s.\n')
        generate_report.get_report(skill_name, (time1 - time0)/len(skills), time3 - time2, time4 - time3, time5 - time4, time6 - time5, intent_number, slot_number, sample_number, function_number)


def main(root_path, multi_skills = 0):
    # each folder means one author, one folder might have several skills
    x = os.system('mkdir results')
    root_path = os.path.abspath(root_path)
    if multi_skills == '1':
        folders = os.listdir(root_path)
        folders.sort()
        for folder in tqdm(folders):
            check_skill(root_path, folder)  
    else:
        check_skill(root_path, '')



if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

