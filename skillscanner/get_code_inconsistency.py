import os
import csv
import json

noun_one_word = open('noun_one_word.txt').read().split('\n')[:-1]
noun_two_word = open('noun_two_word.txt').read().split('\n')[:-1]
unique_noun = ['user', 'name', 'person']


def read_outputs_data_collection(skill_name):
    data_collection_outputs = []
    with open('results/' + skill_name + '/content_safety/outputs_data_collection.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            data_collection_outputs.append(row)
    return data_collection_outputs


def write_results(filename, outputs):
    with open('results/' + filename, 'w', newline = '') as f: 
        writer = csv.writer(f)
        for output in outputs:
            x = writer.writerow(output)


def get_intent_content(skill):
    try:
        intent_content = json.loads(open(skill['intent_file']).read())
    except:
        return {}
    content = ''
    if 'intents' in intent_content.keys():
        content = intent_content
    if 'languageModel' in intent_content.keys():
        content = intent_content['languageModel']
    if 'interactionModel' in intent_content.keys():
        content = intent_content['interactionModel']['languageModel']
    return content


### Skill invocation name issues

#1  One-word invocation names are not allowed, unless: brand/two or more words
#2  Two-word invocation names with one as definite article (the a an ...)
#3  must not contain any of the Alexa skill launch phrases and connecting words
#  "run," "start," "play," "resume," "use," "launch," "ask," "open," "tell," "load," "begin," and "enable."
#  "to," "from," "in," "using," "with," "about," "for," "that," "by," "if," "and," "whether."
#4  must not contain the wake words "Alexa," "Amazon," "Echo," or the words "skill" or "app".
#5  only lower-case alphabetic characters/numbers must be spelled out 


def get_word_issue_skill(invocation_name):
    word_issues = {}
    two_words_banned = ['the', 'a', 'an', "for", "to", "of," "about," "up," "by," "at," "off," "with"]
    alexa_words_banned = ["run", "start", "play", "resume", "use", "launch", "ask", "open", "tell", "load", "begin", "enable"]
    alexa_words_banned = alexa_words_banned + ["Alexa", "Amazon", "Echo", "skill", "app"]
    alexa_words_banned = alexa_words_banned + ["to", "from", "in", "using", "with", "about", "for", "that", "by", "if", "and", "whether"]
    words = invocation_name.split()
    if len(words) == 1:
        word_issues['one_word'] = 1
    if len(words) == 2:
        if any (word in words for word in two_words_banned):
            word_issues['two_word'] = 1
    if any (word in words for word in alexa_words_banned):
        word_issues['alexa_words'] = 1
    for char in invocation_name:
        if char.isupper() or char.isnumeric():
            word_issues['not_lower_case'] = 1
            break
    return word_issues


def get_skill_invocation_name_issue(skill_name, skill):
    content = get_intent_content(skill)
    try:
        invocation_name = content['invocationName']
    except:
        invocation_name = ''
    word_issues = get_word_issue_skill(invocation_name)
    with open('results/' + skill_name +'/content_safety/invocation_name_issue.txt', 'w') as f:
        for issue in word_issues:
            x = f.write(issue + '\n')


def get_intents(skill):
    content = get_intent_content(skill)
    try:
        intents = content['intents']
    except:
        return []
    results = []
    for intent in intents:
        try:
            name = intent['name']
        except:
            name = intent['intent']  
        # remove Amazon built in intents: Cancle, Stop, Help, etc.
        if 'AMAZON' in name:
            continue 
        samples = []
        # get intent samples
        if 'samples' in intent:
            samples = intent['samples']
        elif 'phrases' in intent:
            samples = intent['phrases']
        else:
            samples = []
        if 'slots' in intent:
            slots = intent['slots']
            for slot in slots:
                # put all samples together
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


def spit_slot_name(slot):
    if 'alexa' in slot:
        slot = slot['alexa']
    elif 'dialogflow' in slot:
        return ""
    if 'AMAZON' in slot:
        slot = slot.replace('AMAZON.', '')
    if slot.isupper() or '_' in slot:
        words = slot.lower().split('_')
    else: 
        words = []
        word = ''
        for i in slot:
            if i.islower():
                word = word + i
            else:
                words.append(word.lower())
                word = i
        words.append(word.lower())
        if words[0] == '':
            words = words[1:]
    return words


def get_data_collection_slots(slots):
    data_collection_slots = []
    for slot in slots:
        slot_name_words = spit_slot_name(slot['name'])
        if len(set(noun_one_word) & set(slot_name_words)) > 0:
            data_collection_slots.append(slot)
        if any (word in ' '.join(slot_name_words) for word in noun_two_word):
            data_collection_slots.append(slot)
        if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
            data_collection_slots.append(slot)
        if 'type' not in slot:
            continue
        slot_name_words = spit_slot_name(slot['type'])
        if  len(set(noun_one_word) & set(slot_name_words)) > 0:
            data_collection_slots.append(slot)
        if any (word in ' '.join(slot_name_words) for word in noun_two_word):
            data_collection_slots.append(slot)
        if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
            data_collection_slots.append(slot)
    return data_collection_slots


def get_slot_collected_data_type(slot):
    slot_name_words = spit_slot_name(slot['name'])
    if len(set(noun_one_word) & set(slot_name_words)) > 0:
        data_type = list(set(noun_one_word) & set(slot_name_words))[0]
    for word in noun_two_word:
        if word in ' '.join(slot_name_words):
            data_type = word
    if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
        data_type =  slot_name_words[0]
    if 'type' not in slot:
        return data_type
    slot_name_words = spit_slot_name(slot['type'])
    if len(set(noun_one_word) & set(slot_name_words)) > 0:
        data_type = list(set(noun_one_word) & set(slot_name_words))[0]
    for word in noun_two_word:
        if word in ' '.join(slot_name_words):
            data_type = word
    if len(slot_name_words) == 1 and slot_name_words[0] in unique_noun:
        data_type = slot_name_words[0]
    return data_type


## whether answer in intent sample 
# 1 have 0 not 2 not sure 4 mix
def get_data_collection_intents(slot_samples):         
    intents = {}
    for result in slot_samples:
        intent_name, slot, sample = result
        index = intent_name
        if index not in intents:
            intents[index] = {}
        if slot['name'] not in intents[index]:
            intents[index][slot['name']] = []
        # intent doesn't have sample
        if sample == "":
            intents[index][slot['name']].append((slot, -1, sample))
        # intent has sample like "{name}" and not sure whether data collection
        elif sample == '{' + slot['name'] + '}':
            intents[index][slot['name']].append((slot, 2, sample))
        # intent has data collection
        # this is too simple ("i am" is missed, "my cat name is" can cause false positive)
        elif 'my' in sample.lower() or 'i am' in sample.lower():
            intents[index][slot['name']].append((slot, 1, sample))
        # intent has samples but no data collection
        else:
            intents[index][slot['name']].append((slot, 0, sample))
    data_collection_intents = {}
    for i in intents:
        data_collection_intents[i] = []
        for slot in intents[i]:
            values = [j[1] for j in intents[i][slot]]
            # the intent doesn't have any sample
            if -1 in values:
                data_collection_intents[i].append((intents[i][slot][0][0], -1))
            # have sample and data collection
            elif 1 in values:
                data_collection_intents[i].append((intents[i][slot][0][0], 1))
            # have sample and no data collection
            elif 0 in values:
                data_collection_intents[i].append((intents[i][slot][0][0], 0))
            # have sample and not sure whether for data collection ("{name}")
            else:
                data_collection_intents[i].append((intents[i][slot][0][0], 2))
    return data_collection_intents


def get_slot_samples(skill):
    try:
        intents = get_intents(skill)
    except:
        return [], []
    slot_samples = []
    intent_no_samples = []
    for intent in intents:
        intent_name, slots, samples = intent
        if len(samples) == 0:
            intent_no_samples.append((intent_name, ""))
        data_collection_slots = get_data_collection_slots(slots)
        for data_collection_slot in data_collection_slots:
            k = 0
            for sample in samples:
                if '{' + data_collection_slot['name'] + '}' in sample:
                    slot_samples.append((intent_name, data_collection_slot, sample))
                    k = k +1
            if k == 0:
                slot_samples.append((intent_name, data_collection_slot, ""))
    return intent_no_samples, slot_samples


def get_intent_output_issues(data_collection_intents, data_collection_outputs):
    data_collection_intents_outputs = []
    data_collection_intents_no_outputs = []
    data_collection_no_intents_outputs = []
    output_done = {}
    slot_done = {}
    for intent in data_collection_intents:
        if 'birthday' in intent.lower():
            continue
        for slot in data_collection_intents[intent]:
            slot, slot_issue = slot
            # the slot doesn't collect user data,
            if slot_issue == 0:
                continue
            slot_data_type = get_slot_collected_data_type(slot)
            if 'name' in slot_data_type:
                slot_data_type = 'name'
            # if no outputs, all the intents and slots are "intent no output"
            if data_collection_outputs == []:
                data_collection_intents_no_outputs.append((intent, slot, slot_issue))
                continue
            for output in data_collection_outputs:
                filename, output, output_data_type = output
                if output_data_type[13:] in slot_data_type:
                    if (intent, slot, slot_issue) not in data_collection_intents_outputs:
                        #data_collection_intents_outputs.append((filename, output, intent, slot, slot_issue, slot_data_type))
                        data_collection_intents_outputs.append((filename, intent, slot_issue, slot['name'], slot['type'], slot_data_type))
                    output_done[(filename, output, output_data_type)] = 1
                    slot_done[(intent, slot['name'])] = 1
            # if don't find an output for the slot, the slot is in "intent no output"
            if (intent, slot['name']) not in slot_done:
                data_collection_intents_no_outputs.append((filename, intent, slot_issue, slot['name'], slot['type'], slot_data_type))
    # if the output is not used in previous mapping, the output is in "output no intent"
    for output in data_collection_outputs:
        filename, output, output_data_type = output
        if output_data_type == 'collect data birthday':
            continue
        if (filename, output, output_data_type) not in output_done:
            data_collection_no_intents_outputs.append((filename, output, output_data_type))
    return data_collection_intents_outputs, data_collection_no_intents_outputs, data_collection_intents_no_outputs 


# data collection "slot no samples"
def get_no_samples(data_collection_intents):
    data_collection_slots_no_samples = []
    for intent in data_collection_intents:
        for slot in data_collection_intents[intent]:
            slot, slot_issue = slot
            if slot_issue == -1:
                data_collection_slots_no_samples.append(intent)
    return data_collection_slots_no_samples


def get_birthday_intents(skill, data_collection_outputs):
    intents = get_intents(skill)
    data_collection_intents_outputs = []
    data_collection_no_intents_outputs = []
    data_collection_intents_no_outputs = []
    birthday_intents = []
    for intent in intents:
        intent_name, slots, samples = intent
        if 'birthday' in intent_name.lower():
            slots_names = [slot['name'] for slot in slots]
            if 'year' in slots_names and 'month' in slots_names and 'day' in slots_names:
                for slot in slots:
                    birthday_intents.append((intent, slot, 1))
    birthday_outputs = []
    for output in data_collection_outputs:
        filename, output, data_type = output
        if data_type == 'collect data birthday':
            birthday_outputs = [(filename, output, data_type)]
    if len(birthday_intents) > 0 and len(birthday_outputs) > 0:
        for slot in birthday_intents:
            data_collection_intents_outputs.append((birthday_outputs[0], slot[0], slot[1]['type'], slot[1]['name'], 0))
    if len(birthday_intents) == 0 and len(birthday_outputs) > 0:
        data_collection_no_intents_outputs.append(birthday_outputs[0])
    if len(birthday_intents) > 0 and len(birthday_outputs) == 0:
        data_collection_intents_no_outputs.append(birthday_intents[0])
    return data_collection_intents_outputs, data_collection_no_intents_outputs, data_collection_intents_no_outputs


def get_code_inconsistency(skill_name, skill):
    intent_no_samples, slot_samples = get_slot_samples(skill)
    data_collection_intents = get_data_collection_intents(slot_samples)
    data_collection_outputs = read_outputs_data_collection(skill_name)
    data_collection_intents_outputs, data_collection_no_intents_outputs, data_collection_intents_no_outputs  = get_intent_output_issues(data_collection_intents, data_collection_outputs)
    data_collection_intents_outputs_birthday, data_collection_no_intents_outputs_birthday, data_collection_intents_no_outputs_birthday = get_birthday_intents(skill, data_collection_outputs)
    data_collection_intents_outputs  = data_collection_intents_outputs + data_collection_intents_outputs_birthday
    data_collection_no_intents_outputs = data_collection_no_intents_outputs + data_collection_no_intents_outputs_birthday
    data_collection_intents_no_outputs = data_collection_intents_no_outputs + data_collection_intents_no_outputs_birthday
    data_collection_slots_no_samples = get_no_samples(data_collection_intents)
    write_results(skill_name + "/code_inconsistency/intent_output.csv", data_collection_intents_outputs)
    write_results(skill_name + "/code_inconsistency/output_no_intent.csv", data_collection_no_intents_outputs)       # 6.6.1
    write_results(skill_name + "/code_inconsistency/intent_no_output.csv", data_collection_intents_no_outputs)       # 6.6.2
    write_results(skill_name + "/code_inconsistency/intent_no_sample.csv", intent_no_samples)                        # 6.6.3
    write_results(skill_name + "/code_inconsistency/slot_no_sample.csv", data_collection_slots_no_samples)           # 6.6.3

