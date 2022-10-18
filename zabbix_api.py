import requests
import json
from ssh_connect import connect
zabbix_server = 'your server/api_jsonrpc.php' #insert your server 
TOKEN = '' #token

def get_rules():
    get_rules={
        "jsonrpc": "2.0",
        "method": "drule.get",
        "params": {
            "output": "extend",
        },
        "auth": TOKEN,
        "id": 1
    }
    r = requests.post(zabbix_server, json=get_rules)
    rules = {}
    #print((r.json()))
    for rule in r.json()["result"]:
        rules[rule['druleid']] = rule['name']
        #print(rule['druleid'], rule['name'], rule['iprange'], '\n')
    return rules


def make_inv():
    rules = get_rules()
    params = {"output": "extend",
              "selectDServices": "extend"}
    get_hosts = \
            {
                "jsonrpc": "2.0",
                "method": "dhost.get",
                "params": params,
                "auth": TOKEN,
                "id": 1
            }
    r = requests.post(zabbix_server, json=get_hosts)
    inventory_dict = {}
    active_hosts = []
    for hosts in r.json()['result']:
        host = hosts['dservices'][0]
        if host['status'] == "1":
            active_hosts.append((hosts['druleid'], host["ip"], host["dns"]))
    #print(active_hosts)
    for value, rule_name in rules.items():
        inventory_dict[rule_name] = f'[{rule_name}]\n'
        for host in active_hosts:
            if host[0] == value:
                if host[2] != '':
                    inventory_dict[rule_name] += host[1] + '    #   ' + host[2] + '\n'
                else:
                    inventory_dict[rule_name] += host[1] + '\n'
        inventory_dict[rule_name] += '\n\n\n'
    #print(rules)
    with open("zabbix_inventory.ini", "w", encoding='utf=8') as inv_file:
        for groups in inventory_dict.values():
            inv_file.write(groups)


def make_inv_file(hosts, filename):
    with open(f"{filename}.inv", "w", encoding='utf=8') as inv_file:
        for host in hosts.values():
            if host['ip']:
                inv_file.writelines(host['ip'] + '    #   ' + host['name'] + '\n')
            else:
                inv_file.writelines(host['dns'] + '    #   ' + host['name'] + '\n')


def get_groups():
    get_groups = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "output": "extend",
        },
        "auth": TOKEN,
        "id": 1
    }
    r = requests.post(zabbix_server, json=get_groups)
    groups = {}
    # print((r.json()))
    for group in r.json()["result"]:
        groups[group['groupid']] = group['name']
    return groups

get_groups()

def find_groups(groups):
    params = {"output": "extend",
              "filter": {"name": groups}}
    get_hostgroups = \
            {
                "jsonrpc": "2.0",
                "method": "hostgroup.get",
                "params": params,
                "auth": TOKEN,
                "id": 1
            }
    host_groups = requests.get(zabbix_server, json=get_hostgroups)
    ids = []
    for gr in host_groups.json()['result']:
        ids.append(gr['groupid'])
    return ids

def find_hosts(ids):
    params = {"output": "extend",
              "groupids": ids}
    get_hosts = \
            {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": params,
                "auth": TOKEN,
                "id": 1
            }
    zabbix_hosts = requests.get(zabbix_server, json=get_hosts)
    hosts = {}
    for host in zabbix_hosts.json()['result']:
        hosts[host['hostid']] = {'name': host['name'], 'ip': ''}

    params = {"output": "extend",
              "hostids": list(hosts.keys())}
    get_hosts_interface = \
        {
            "jsonrpc": "2.0",
            "method": "hostinterface.get",
            "params": params,
            "auth": TOKEN,
            "id": 1
        }
    sw_ips = requests.get(zabbix_server, json=get_hosts_interface)
    for interface in sw_ips.json()['result']:
        if interface['useip'] == '1':
            hosts[interface['hostid']]['ip'] = interface['ip']
        else:
            hosts[interface['hostid']]['dns'] = interface['dns']
    return hosts

#make_inv(rules)
#
#groups = ['SYSTEM: hypervisors']

groups = get_groups()
for k, value in groups.items():
        value = value.replace(' ', '_')
        make_inv_file(find_hosts(k), value)

# hosts = find_hosts(find_groups(groups))
# for g in groups:
#     make_inv_file()

#make_inv()
