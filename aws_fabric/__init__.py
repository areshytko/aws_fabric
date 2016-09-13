
import boto3
import logging
import json
from fabric.api import *

logging.basicConfig(level=logging.INFO)

with open('config.json', 'r') as cf:
    config = json.load(cf)
    env.region = config['aws_region']
    env.azone = config['availability_zone']
    env.ec2 = boto3.client('ec2', region_name=env.region)


__all__ = ['ec2']
