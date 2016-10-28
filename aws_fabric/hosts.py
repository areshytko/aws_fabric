
import os.path
import json


class Hosts(object):
    """
    hosts persistent cache
    """

    def __init__(self, filename):
        self.filename = filename
        self.hosts = []
        if os.path.exists(filename):
            with open(filename, 'r') as hosts_file:
                self.hosts += json.load(hosts_file)

    def get_ips(self):
        return [i['ip'] for i in self.hosts]

    def get_host(self, ip):
        return [x for x in self.hosts if x['ip'] == ip][0]

    def add_ec2_instances(self, instances):
        self.hosts += [{'ip': i.public_ip, 'id': i.instance_id, 'type': 'ec2'} for i in instances]

    def remove_ec2_instances(self, instance_ids):
        self.hosts = filter(lambda h: h['id'] not in instance_ids, self.hosts)

    def dump(self):
        with open(self.filename, 'w') as hosts_file:
            json.dump(self.hosts, hosts_file)

__all__ = ["Hosts"]