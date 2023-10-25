import os

skills = os.listdir('results')
x = os.system('mkdir summary')

for skill in skills:
    report = open('results/' + skill + '/report.txt').read().split('\n')[:-1]
    for line in report[6:]:
        if line == ['']:
            continue
        if 'issue' in line.lower():
            continue
        with open('summary/' + line.split('\t')[0].split(':')[0].replace('/','_') + '.txt', 'a') as f:
            x = f.write(skill + '\n')
    