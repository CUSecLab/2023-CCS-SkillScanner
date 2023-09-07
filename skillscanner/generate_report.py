## generate report for each skill
import csv

# read results
def read_results(filename):
    with open(filename) as f:
        reader = csv.reader(f)
        outputs = []
        for row in reader:
            outputs.append([filename.split('/')[-1][:-4].replace('_', ' ')] + row)
    return outputs


def write_all_results(skill_name, results):
    with open('results/' + skill_name + 'all_results.csv', 'a', newline = '') as f: 
        writer = csv.writer(f)
        for result in results:
            x = writer.writerow(result)


def get_content_safety(skill_name):
    all_issues = []
    all_issues.append(['\nData collection in the skill code:'])
    all_issues = all_issues + read_results('results/' + skill_name + '/content_safety/outputs_data_collection.csv')
    all_issues = all_issues + [['permission data collection', i[2]] for i in read_results('results/' + skill_name + '/privacy_violation/permissions.csv')]
    all_issues.append(['\nIssues in the skill code:'])
    all_issues = all_issues + read_results('results/' + skill_name + '/content_safety/outputs_positive_rating.csv')
    all_issues = all_issues + read_results('results/' + skill_name + '/content_safety/outputs_toxic.csv')
    all_issues = all_issues + read_results('results/' + skill_name + '/content_safety/malicious_html.csv')
    all_issues = all_issues + open('results/' + skill_name + '/content_safety/category_data_collection.txt').read().split('\n')
    all_issues = all_issues + open('results/' + skill_name + '/content_safety/invocation_name_issue.txt').read().split('\n')
    all_issues = all_issues + open('results/' + skill_name + '/content_safety/health_lack_disclaimer.txt').read().split('\n')
    return all_issues


def get_code_inconsistency(skill_name):
    all_issues = []
    all_issues = all_issues + read_results('results/' + skill_name + '/code_inconsistency/intent_no_output.csv')
    all_issues = all_issues + read_results('results/' + skill_name + '/code_inconsistency/output_no_intent.csv')
    all_issues = all_issues + read_results('results/' + skill_name + '/code_inconsistency/intent_no_sample.csv')
    all_issues = all_issues + read_results('results/' + skill_name + '/code_inconsistency/slot_no_sample.csv')
    return all_issues


def get_privacy_violation(skill_name):
    all_issues = []
    all_issues = all_issues + [[issue] for issue in open('results/' + skill_name + '/privacy_violation/privacy_policy_result.txt').read().split('\n')]
    all_issues = all_issues + [[issue] for issue in open('results/' + skill_name + '/privacy_violation/disclosure_to_alexa.txt').read().split('\n')]
    return all_issues

def get_taint_analysis(skill_name):
    all_issues = []
    all_issues = all_issues + [i[:2] for i in read_results('results/' + skill_name + '/taint_analysis/permissions_asked_not_called.csv')]
    all_issues = all_issues + [i[:2] for i in read_results('results/' + skill_name + '/taint_analysis/permissions_asked_not_used.csv')]
    all_issues = all_issues + [i[:2] for i in read_results('results/' + skill_name + '/taint_analysis/permissions_called_not_asked.csv')]
    all_issues = all_issues + [i[:2] for i in read_results('results/' + skill_name + '/taint_analysis/slots_asked_not_used.csv')]
    return all_issues


def get_report(skill_name, time_index, time_content, time_code, time_privacy, time_taint, intent_number, slot_number, sample_number, function_number):
    all_issues = []
    all_issues = all_issues + get_content_safety(skill_name)
    all_issues = all_issues + get_code_inconsistency(skill_name)
    all_issues = all_issues + get_privacy_violation(skill_name)
    try:
        all_issues = all_issues + get_taint_analysis(skill_name)
    except:
        all_issues = all_issues + []

    with open('results/' + skill_name + '/report.txt', 'w') as f:
        x = f.write(str(time_index) + '\t' + str(time_content) + '\t' + str(time_code) + '\t' + str(time_privacy) + '\t' + str(time_taint) + '\n')
        #x = f.write('Scanning the skill cost: ' + str(time_index + time_content + time_code + time_privacy + time_taint) + 's.\n')
        x = f.write('The intent number is: ' + str(intent_number) + '\n')
        x = f.write('The slot number is: ' + str(slot_number) + '\n')
        x = f.write('The function number is: ' + str(function_number) + '\n')
        x = f.write('The sample number is: ' + str(sample_number) + '\n')

        for issue in all_issues:
            if issue == '' or issue == ['']:
                continue
            for i in issue:
                x = f.write(i + '\t')
            x = f.write('\n')
        
        
