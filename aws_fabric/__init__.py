
import os.path
import boto3
import logging
import json
from fabric.api import *

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as cf:
    config = json.load(cf)
    env.region = config['aws_region']
    env.azone = config['availability_zone']
    env.hosts_file = config['hosts_file']
    env.user = config['user']

env.ec2 = boto3.client('ec2', region_name=env.region)

if os.path.isfile(env.hosts_file):
    with open(env.hosts_file, 'r') as hosts_file:
        env.hosts = [i['ip'] for i in json.load(hosts_file)]

__all__ = ['ec2', 'common']
