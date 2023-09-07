import os
import csv
import json
import time
from collections import deque


class Graph:
    def __init__(self, edges, n):
        self.adjList = [[] for _ in range(n)]
        for (src, dest) in edges:
            self.adjList[src].append(dest)


def isReachable(graph, src, dest, discovered, path):
    discovered[src] = True
    path.append(src)
    if src == dest:
        return True
    for i in graph.adjList[src]:
        if not discovered[i]:
            if isReachable(graph, i, dest, discovered, path):
                return True
    path.pop()
    return False


def write_results(filename, outputs):
    with open('results/' + filename, 'w', newline = '') as f: 
        writer = csv.writer(f)
        for output in outputs:
            x = writer.writerow(output)


def read_response(skill):
    responses = []
    with open('results/' + skill['root'].replace('/', '~').replace(' ', '@') + '/content_safety/response.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            responses.append(row)
    responses = [':'.join([response[0].replace(skill['root'] + '/', '')] + response[2:]) for response in responses]
    return responses


def read_all_flow(filename):
    flows = []
    with open(filename) as f:
        reader = csv.reader(f, delimiter = '\n', quoting = csv.QUOTE_NONE)
        for row in reader:
            try:
                source, sink = row[0].replace('""', '"').split('source: ')[1].split('"warning","')[0].split('","/')[0].split(' \t sink: ')
                flows.append((source, sink))
            except:
                continue
    flows2 = []
    for flow in set(flows):
        try:
            flows2.append((flow[0][3:-3].split('"|"relative:///')[1], flow[1][3:-3].split('"|"relative:///')[1]))
        except:
            continue
    flows = flows2 + get_added_flows(flows2)
    return list(set(flows))


# to get additional flows like: a = b.c(d), b => a
# but this function is very slow because it compares two nodes
def get_added_flows(flows):
    added_flows = []
    nodes = list(set([flow[0] for flow in flows] + [flow[1] for flow in flows]))
    nodes.sort()
    nodes = [node.split(':') for node in nodes]
    nodes = [[node[0]] + [int(number) for number in node[1:]] for node in nodes]
    for node1 in nodes:
        for node2 in nodes:
            if node1[3] == node2[3] and node1[1] == node2[1] and node1[0] == node2[0] and node1[2] >= node2[2] and node1[4] <= node2[4]:
                added_flows.append((':'.join([str(i) for i in node1]), ':'.join([str(i) for i in node2])))
    return added_flows


# get all files code content
def get_file_codes(skill, files):
    files_codes = {}
    for file in files:
        with open(skill['root'] + '/' + file) as f:
            files_codes[file] = f.read().split('\n')
    return files_codes


# get code content of a specific node (location)
def get_code_content(flow_node, files_codes):
    file, line1, column1, line2, column2 = flow_node.split(':')
    line1 = int(line1)
    column1 = int(column1)
    line2 = int(line2)
    column2 = int(column2)
    codes = files_codes[file]
    if line1 == line2:
        content = codes[line1 - 1][column1 -1 : column2]
    else:
        content = codes[line1 - 1][column1 -1 :]
        for i in range(line1, line2 - 1):
            content = content + '\n' + codes[i]
        content = content + '\n' + codes[line2 - 1][: column2]
    return content


# get map from node to code
def get_node_to_code(skill, nodes):
    files = set([node.split(':')[0] for node in nodes])
    files_codes = get_file_codes(skill, files)
    node_to_code = {}
    for node in nodes:
        node_to_code[node] = get_code_content(node, files_codes)
    return node_to_code


# we only get slots from the flows now
# also remove node across several lines
def get_slot_from_flow(flows, node_to_code):
    slots = []
    endpoints = ['.slots', 'getslot', '.get_slot']
    for flow in flows:
        try:
            code = node_to_code[flow[0]]
        except:
            continue
        if any (endpoint in code.lower().replace('@', '') for endpoint in endpoints):
            # remove node with several lines of code (such as a large json)
            if '\n' in code:
                continue
            slots.append(flow[0])
    return list(set(slots))


# we only get permissions from the flows now
def get_permission_from_flow(flows, node_to_code):
    permissions = []
    # 1 permissions with endpoints
    endpoints = ['v1/devices', 'v2/accounts', 'v2/persons']
    # 2 permissions from service_client_factory.ups_service_client/device_address_service_client
    endpoints = endpoints + ['serviceclientfactory.getupsservice', 'serviceclientfactory.getdeviceaddressservice']
    # 3 permission from context.geolocation
    endpoints = endpoints + ['context.geolocation']
    for flow in flows:
        try:
            code = node_to_code[flow[0]]
        except:
            continue
        if any (endpoint in code.lower().replace('_', '') for endpoint in endpoints):
            # remove node with several lines of code (such as a large json)
            if '\n' in code:
                continue
            permissions.append(flow[0])
    return list(set(permissions))


def get_database_from_flow(flows, node_to_code):
    databases = []
    endpoints = ['dynamodb']
    for flow in flows:
        try:
            code = node_to_code[flow[0]]
        except:
            continue
        if any (endpoint in code.lower().replace('_', '') for endpoint in endpoints):
            # remove node with several lines of code (such as a large json)
            if '\n' in code:
                continue
            databases.append(flow[0])
    return list(set(databases))


def is_false_nodes(node):
    start_line, start_column, end_line, end_column = node.split(':')[1:5]
    if int(start_line) == int(end_line):
        if int(start_column) >= int(end_column):
            return True
        else:
            return False
    else:
        return True


# transfer all flow nodes to a list of number and edges with number
def get_edges(flows):
    node_to_number = {}
    number_to_node = {}
    edges = []
    for flow in flows:
        source, sink = flow
        # check if source is useful
        if is_false_nodes(source) or is_false_nodes(sink):
            continue
        if source not in node_to_number:
            node_to_number[source] = len(node_to_number)
            number_to_node[len(number_to_node)] = source
        if sink not in node_to_number:
            node_to_number[sink] = len(node_to_number)
            number_to_node[len(number_to_node)] = sink
        edges.append((node_to_number[source], node_to_number[sink]))
    return node_to_number, number_to_node, edges 


def get_data_used_in_response(slots_called, slots_asked, responses, node_to_number, number_to_node, edges, node_to_code):
    n = len(node_to_number)
    graph = Graph(edges, n)
    paths = []
    for slot in slots_called:
        src = node_to_number[slot]
        for response in responses:
            if response not in node_to_number:
                continue
            dest = node_to_number[response]
            path = deque()
            discovered = [False] * n
            if isReachable(graph, src, dest, discovered, path):
                paths.append(path)
    slot_names_used = []
    for path in paths:
        for flow_node in path:
            code_content = node_to_code[number_to_node[flow_node]]
            for slot_name in slots_asked:
                if slot_name.lower() not in code_content.lower():
                    continue
                if slot_name in slot_names_used:
                    continue
                slot_names_used.append(slot_name)
                if slot_names_used == slots_asked:
                    return slots_asked                     
    return slot_names_used


def find_path(source, edges):
    todo = [source]
    done = []
    while todo != []:
        thisnode = todo[0]
        todo.remove(thisnode)
        done.append(thisnode)
        for edge in edges:
            if edge[0] == thisnode:
                if edge[1] in todo or edge[1] in done:
                    continue
                todo.append(edge[1])
    return done


def get_data_used_in_database(slots_called, slots_asked, databases, node_to_number, number_to_node, edges, node_to_code):
    n = len(node_to_number)
    graph = Graph(edges, n)
    slot_names_used = []
    for slot in slots_called:
        source1 = node_to_number[slot]
        for database in databases:
            try:
                source2 = node_to_number[database]
            except:
                continue
            sink1 = find_path(source1, edges)
            sink2 = find_path(source2, edges)
            if len(set(sink1) & set(sink2)) == 0:
                continue
            path = deque()
            discovered = [False] * n
            if isReachable(graph, source1, min(list(set(sink1) & set(sink2))), discovered, path):
                for flow_node in path:
                    code_content = node_to_code[number_to_node[flow_node]]
                    for slot_name in slots_asked:
                        if slot_name.lower() in code_content.lower():
                            if slot_name not in slot_names_used:
                                slot_names_used.append(slot_name)
    return slot_names_used


def get_sinks_with_word(node_to_number, node_to_code, edges, source, words):
    sinks = []
    n = len(node_to_number)
    graph = Graph(edges, n)
    possible_sinks = [node_to_number[node] for node in node_to_number if any (word in node_to_code[node].lower().replace('_', '') for word in words)]
    for sink in possible_sinks:
        path = deque()
        discovered = [False] * n
        if isReachable(graph, source, sink, discovered, path):
            sinks.append(sink)
    return sinks


def get_permission_over_priviledge(permissions_called, permissions_asked, node_to_number, number_to_node, edges, node_to_code):
    # from services (permissions_service) to what permissions got
    # upsservice => service.getprofilename()
    permissions_sinks = []
    for service in permissions_called:
        source = node_to_number[service]
        permissions_sinks = permissions_sinks +  get_sinks_with_word(node_to_number, node_to_code, edges, source, permissions_asked + [i.replace('get', 'getpersons') for i in permissions_asked])
    permission_called = []
    for permission in permissions_sinks:
        code_content = node_to_code[number_to_node[permission]].lower().replace('_', '').replace('getpersons', 'get')
        for permission_name in permissions_asked:
            if permission_name.lower() in code_content:     ## ISSUE: code content might be sth like "error.name", then name permission is covered
                break
        if permission_name in permission_called:
            continue
        permission_called.append(permission_name)
    permission_asked_not_called = []
    for permission in permissions_asked:
        if permission not in set(permission_called):
            permission_asked_not_called.append((permission, 'asked not_called'))
    permission_called_not_asked = []
    for permission in permission_called:
        if permission not in set(permissions_asked):
            permission_called_not_asked.append(permission, 'called_not_asked')
    return permission_asked_not_called, permission_called_not_asked


def get_data_used_in_session(permission_got, permissions_asked, node_to_number, number_to_node, edges, node_to_code):
    # from got permissions to persistentattributes or sessionattributes
    # service.getprofilename() => persistentattributes/sessionattributes
    permission_names_used = []
    words = ['sessionattributes', 'sessionattr']
    if permissions_asked == []:
        return []
    for permission in permission_got:
        if type(permission) == int:
            code_content = node_to_code[number_to_node[permission]].lower().replace('_', '').replace('getpersons', 'get')
            source = permission
        else:
            code_content = node_to_code[permission].lower().replace('_', '').replace('getpersons', 'get')
            source = node_to_number[permission]
        for permission_name in permissions_asked:
            if permission_name.lower() in code_content:
                break
        if permission_name in permission_names_used:
            continue
        if len(get_sinks_with_word(node_to_number, node_to_code, edges, source, words)) > 0:
            permission_names_used.append(permission_name)
    return permission_names_used


def get_data_used_in_persistent(permission_got, permissions_asked, node_to_number, number_to_node, edges, node_to_code):
    # from got permissions to persistentattributes or sessionattributes
    # service.getprofilename() => persistentattributes/sessionattributes
    if permissions_asked == []:
        return []
    permission_names_used = []
    words = ['persistentattributes']
    for permission in permission_got:
        if type(permission) == int:
            code_content = node_to_code[number_to_node[permission]].lower().replace('_', '').replace('getpersons', 'get')
            source = permission
        else:
            code_content = node_to_code[permission].lower().replace('_', '').replace('getpersons', 'get')
            source = node_to_number[permission]
        for permission_name in permissions_asked:
            if permission_name.lower() in code_content:
                break
        if permission_name in permission_names_used:
            continue
        if len(get_sinks_with_word(node_to_number, node_to_code, edges, source, words)) > 0:
            permission_names_used.append(permission_name)
    return permission_names_used


def get_data_used_other_function(permission_got, permissions_asked, node_to_number, number_to_node, edges, node_to_code):
    # from got permissions to functions
    # service.getprofilename() => 'send_email'
    if permissions_asked == []:
        return []
    permission_names_used = []
    lists = [['send','email'], ['appointment'], ['order']]
    possible_sinks =[]
    n = len(node_to_number)
    graph = Graph(edges, n)
    for node in node_to_number:
        code = node_to_code[node]
        for words in lists:
            if any (word not in code for word in words):
                continue
            possible_sinks.append(node_to_number[node])
    for permission in set(permission_got):
        if type(permission) == int:
            code_content = node_to_code[number_to_node[permission]].lower().replace('_', '').replace('getpersons', 'get')
            source = permission
        else:
            code_content = node_to_code[permission].lower().replace('_', '').replace('getpersons', 'get')
            source = node_to_number[permission]
        for permission_name in permissions_asked:
            if permission_name.lower() in code_content:
                break
        if permission_name in permission_names_used:
            continue
        for sink in possible_sinks:
            path = deque()
            discovered = [False] * n
            if isReachable(graph, source, sink, discovered, path):
                permission_names_used.append(permission_name)
    return list(set(permission_names_used))


def get_slots(skill_name, flows, node_to_code):
    # get all data collection skills with intent (slot)
    with open('results/' + skill_name + '/code_inconsistency/intent_output.csv') as f:
        reader = csv.reader(f)
        data_collection_slots = []
        for row in reader:
            data_collection_slots.append(row)
    if data_collection_slots == []:
        return [], []
    slots_asked = list([slot[3] for slot in data_collection_slots])
    # get what slots called in code. Now we only get slots from flows.
    slots_called = get_slot_from_flow(flows, node_to_code)
    return slots_called, slots_asked


def get_permissions(skill_name, flows, node_to_code):
    permissions_asked = []
    with open('results/' + skill_name + '/privacy_violation/permissions.csv') as f:
        reader = csv.reader(f)
        for row in reader:
            permissions_asked.append(row[1])
    permissions_called = get_permission_from_flow(flows, node_to_code)
    return permissions_called, permissions_asked


def get_data_usage(data_called, data_asked, responses, databases, node_to_number, number_to_node, edges, node_to_code, skill_name, data_type):
    used_response = get_data_used_in_response(data_called, data_asked, responses, node_to_number, number_to_node, edges, node_to_code)
    used_response = [(slot, 'used in response') for slot in used_response]
    used_database = get_data_used_in_database(data_called, data_asked, databases, node_to_number, number_to_node, edges, node_to_code)
    used_session = get_data_used_in_session(data_called, data_asked, node_to_number, number_to_node, edges, node_to_code)
    used_persistent = get_data_used_in_persistent(data_called, data_asked, node_to_number, number_to_node, edges, node_to_code)
    used_database = [(slot, 'used in database') for slot in used_database + used_session + used_persistent]
    used_other_function = get_data_used_other_function(data_called, data_asked, node_to_number, number_to_node, edges, node_to_code)
    used_other_function = [(slot, 'used in other function') for slot in used_other_function]
    not_used = [slot for slot in data_asked if slot not in [i[0] for i in used_response + used_database + used_other_function]]    
    not_used = [(slot, 'not used') for slot in not_used]
    write_results(skill_name + '/taint_analysis/' + data_type + '_used_response.csv', used_response)
    write_results(skill_name + '/taint_analysis/' + data_type + '_used_database.csv', used_database)
    write_results(skill_name + '/taint_analysis/' + data_type + '_used_other_function.csv', used_other_function)
    write_results(skill_name + '/taint_analysis/' + data_type + '_asked_not_used.csv', not_used)
    if len(used_database) > 0:
        try:
            privacy_policy_content = open('results/' + skill_name + '/privacy_violation/privacy_policy.txt').read()
        except:
            privacy_policy_content = ''
        if 'keep' not in privacy_policy_content or 'retain' not in privacy_policy_content or 'store' not in privacy_policy_content:
            with open('results/' + skill_name + '/privacy_violation/privacy_policy_result.txt', 'a') as f:
                x = f.write("This skill has an incomplete/lacks a privacy policy: data " + str([i[1] for i in used_database]) + " collected and stored in " + data_type + " is not mentioned in privacy policy.\n")

    

def get_taint_analysis(skill_name):
    skill = json.loads(open('results/' + skill_name + '/skill.json').read())
    # remove skills with too many flows (file too large) because hard to process
    try:
        if os.stat('results/' + skill_name + '/taint_analysis/allflow.csv').st_size > 10000000:
            print('Skill flow too large.\n')
            return None
    except:
        print('Failed to get data flow.\n')
        return None
    # get all flows from codeql, some skills might fail to get results
    flows = read_all_flow('results/' + skill_name + '/taint_analysis/allflow.csv')
    # get all nodes from flows and transfer node to number for later processing
    node_to_number, number_to_node, edges = get_edges(flows)
    try:
        node_to_code = get_node_to_code(skill, node_to_number)
    except:
        print('Failed to get code of skill.')
        return None
    responses = read_response(skill)
    databases = get_database_from_flow(flows, node_to_code)

    slots_called, slots_asked = get_slots(skill_name, flows, node_to_code)
    get_data_usage(slots_called, slots_asked, responses, databases, node_to_number, number_to_node, edges, node_to_code, skill_name, 'slots')

    permissions_called, permissions_asked = get_permissions(skill_name, flows, node_to_code)
    get_data_usage(permissions_called, permissions_asked, responses, databases, node_to_number, number_to_node, edges, node_to_code, skill_name, 'permissions')

    permissions_asked_not_called, permissions_called_not_asked = get_permission_over_priviledge(permissions_called, permissions_asked, node_to_number, number_to_node, edges, node_to_code)
    write_results(skill_name + '/taint_analysis/permissions_asked_not_called.csv', permissions_asked_not_called)
    write_results(skill_name + '/taint_analysis/permissions_called_not_asked.csv', permissions_called_not_asked)

    del flows


