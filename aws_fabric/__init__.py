
import os.path
import boto3
import logging
import json
from fabric.api import *
import hosts

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as cf:
    config = json.load(cf)
    env.region = config['aws_region']
    env.azone = config['availability_zone']
    env.hosts_file = config['hosts_file']
    env.user = config['user']

env.ec2 = boto3.client('ec2', region_name=env.region)

env.hosts_cache = hosts.Hosts(env.hosts_file)
ips = env.hosts_cache.get_ips()
if ips:
    env.hosts = ips


__all__ = ['ec2', 'common']
