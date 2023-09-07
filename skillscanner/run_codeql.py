import os
import csv
import json
import signal
import subprocess
import get_taint_analysis

def handler(signum, frame):
    print(" ")
    raise Exception(" ")

signal.signal(signal.SIGALRM, handler)


# read all the results
def read_results(filename):
    with open('results/' + filename) as f:
        reader = csv.reader(f)
        results = []
        for row in reader:
            results.append(row)
    return results


def generate_skill_database_command(skill, skill_type):
    command = ""
    command = command + "../codeql-home/codeql"
    command = command + " database create --language=" + skill_type
    command = command + " --source-root " + skill['root'].replace(' ', '\ ')
    command = command + " results/" + skill['root'].replace('/', '~').replace(' ', '@') + "/database"
    command = command + " --overwrite"
    return command


def generate_flow_command(skill, skill_type):
    skill_name = skill['root'].replace('/', '~').replace(' ', '@')
    command = ""
    command = command + "../codeql-home/codeql"
    command = command + " database analyze \"" + "results/" + skill_name + "/database\""
    command = command + " --rerun " + "../vscode-codeql-starter/codeql-custom-queries-" + skill_type + "/code/get_flow.ql"
    command = command + " --format=csv --output=" + "results/" + skill['root'].replace('/', '~').replace(' ', '@') + "/taint_analysis/allflow.csv"
    return command


def get_file_type(files):
    all = ','.join(files)
    results = {}
    results['js'] = all.count('.js')
    results['py'] = all.count('.py')
    results['java'] = all.count('.java')
    sorted_x = sorted(results.items(), key=lambda kv: kv[1])
    return sorted_x[-1][0]


def run_database_command(skill):
    file_types = (set([file.split('.')[-1] for file in skill["code_files"]]))
    file_types = get_file_type(skill["code_files"])
    skill_type = "javascript"
    if "js" in file_types:
        skill_type = "javascript"
    elif "py" in file_types:
        skill_type = "python"
    command = generate_skill_database_command(skill, skill_type)
    try:
        signal.alarm(60)
        p = subprocess.Popen(command, universal_newlines = True, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        out, err = p.communicate()
        signal.alarm(0)
    except:
        pass


def run_flow_command(skill):
    file_types = (set([file.split('.')[-1] for file in skill["code_files"]]))
    file_types = get_file_type(skill["code_files"])
    if "js" in file_types:
        skill_type = "javascript"
    elif "py" in file_types:
        skill_type = "python"
    else:
        skill_type = "java"
    command = generate_flow_command(skill, skill_type)
    try:    
        signal.alarm(60)
        p = subprocess.Popen(command, universal_newlines = True, shell = True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        out, err = p.communicate()
        with open('results/' + skill['root'].replace('/', '~').replace(' ', '@') + '/taint_analysis/log_flow.txt', 'a') as f:
            x = f.write(skill['root'] + '\t' + out.replace('\n', '') + '\t' + str(err) + '\n')
        signal.alarm(0)
    except:
        pass


def run_codeql(skill_name):
    skill = json.loads(open('results/' + skill_name + '/skill.json').read())
    data_collections = read_results(skill_name + '/code_inconsistency/intent_no_output.csv')
    data_collections = data_collections + read_results(skill_name + '/code_inconsistency/intent_output.csv')
    data_collections = data_collections + read_results(skill_name + '/privacy_violation/permissions.csv')
    if len(data_collections) > 0:
        print('This skill contains data collection. Need to do the taint analysis.\n')
        print('Generating database for skill.\n')
        run_database_command(skill)
        print('Generating data flow for skill.\n')
        run_flow_command(skill)
        get_taint_analysis.get_taint_analysis(skill_name)
    else:
        print('This skill doesn\'t contains data collection. Skip the taint analysis.\n')



