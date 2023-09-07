import os
import json
from tqdm import tqdm

### get dataset statistic

# same with 3_get_code_in_consistency.py
def get_intent_content(skill):
    try:
        intent_content = json.loads(open(skill['intent_file']).read())
    except:
        return {}
    if 'intents' in intent_content.keys():
        content = intent_content
    if 'languageModel' in intent_content.keys():
        content = intent_content['languageModel']
    if 'interactionModel' in intent_content.keys():
        content = intent_content['interactionModel']['languageModel']
    return content


# same with 3_get_code_in_consistency.py
def get_intents(skill):
    content = get_intent_content(skill)
    intents = content['intents']
    results = []
    for intent in intents:
        try:
            name = intent['name']
        except:
            name = intent['intent']  
        if 'AMAZON' in name:
            continue 
        samples = []
        if 'samples' in intent:
            samples = intent['samples']
        elif 'phrases' in intent:
            samples = intent['phrases']
        else:
            samples = []
        if 'slots' in intent:
            slots = intent['slots']
            for slot in slots:
                if 'samples' in slot:
                    samples = samples + slot['samples']
        elif 'inputs' in intent:
            slots = intent['inputs']
            for slot in slots:
                if 'phrases' in slot:
                    samples = samples + slot['phrases']
        else:
            slots = []
        results.append((name, slots, samples))
    return results


# get all intent, slot and sample numbers in dataset
def get_dataset_intent_number(skills):
    intents = []
    for skill in skills:
        try:
            intents = get_intents(skill) + intents
        except:
            continue
    print('The total intent number is : ' + str(len(intents)))                                     # intent number
    print('The total slot number is : ' + str(sum([len(intent[1]) for intent in intents])))        # slot number
    print('The total sample number is : ' + str(sum([len(intent[2]) for intent in intents])))      # sample number
    return len(intents), sum([len(intent[1]) for intent in intents]), sum([len(intent[2]) for intent in intents])


# get function number
def get_functions(lines):
    k = 0
    for line in lines:
        # For javascript code, function definition should have: const IntentHandler = {
        if 'const' in line and ('= {' in line or '={' in line) and 'handler' in line:
            k = k + 1
        # For python code, function definition should have: class IntentHandler():
        if '):' in line and 'handler' in line:
            k = k + 1
    return k


def get_dataset_function_number(skills):
    function_number = 0
    for skill in skills:
        for file in skill['code_files']:
            try:
                lines = open(file).read().lower().split('\n')[:-1]
                function_number = function_number + get_functions(lines)
            except:
                continue
    print('The total function number is : ' + str(function_number) + '\n')
    return function_number


def get_dataset_statistic(skills):
    print('---------- Getting Statistic of Dataset ----------')
    intent_number, slot_number, sample_number = get_dataset_intent_number(skills)
    function_number = get_dataset_function_number(skills)
    return intent_number, slot_number, sample_number, function_number
