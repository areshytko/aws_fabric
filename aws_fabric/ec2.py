import json
import boto3
from fabric.api import *
from decorators import *
from fabric.context_managers import settings, hide
import datetime
import math
import logging
import os.path


# @TODO add attach-volume
# @TODO add describe-volumes
# @TODO add create-volume


@task
@runs_once
def regions():
    local("aws ec2 describe-regions")


@task
@runs_once
def zones(region=env.region):
    local("aws ec2 describe-availability-zones --region {}".format(region))


@task
@runs_once
@timing
def up(spec='specification.json', bid=None):
    """
    launches EC2 instance

    For specification file format :
    @see https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.Client.request_spot_instances
    :param spec: specification file
    :param bid: bid price for spot instances
    """

    instances = up_spot(spec, bid) if bid else up_on_demand(spec)
    hosts = [{'ip': i.public_ip, 'id': i.instance_id, 'type': 'ec2'} for i in instances]

    if os.path.exists(env.hosts_file):
        with open(env.hosts_file, 'r') as hosts_file:
            hosts += json.load(hosts_file)

    with open(env.hosts_file, 'w') as hosts_file:
        json.dump(hosts, hosts_file)

    env.hosts += [instance.public_ip for instance in instances]


@task
@runs_once
def terminate(*ids):
    env.ec2.terminate_instances(InstanceIds=ids)
    hosts = []
    with open(env.hosts_file, 'r') as hosts_file:
        hosts = json.load(hosts_file)
    with open(env.hosts_file, 'w') as hosts_file:
        json.dump(filter(lambda h: h['id'] not in ids, hosts), hosts_file)


@task
@runs_once
def ls(all=False):

    def describe_instances(client, region):
        response = client.describe_instances()
        request_responses = SpotInstanceResponse.create(response)
        print
        print "Active instances for region {}:".format(region)
        print
        for resp in request_responses:
            logging.info(resp)

    if all:
        regions = env.ec2.describe_regions()
        for region in [r['RegionName'] for r in regions['Regions']]:
            ec2 = boto3.client('ec2', region_name=region)
            describe_instances(ec2, region)
    else:
        describe_instances(env.ec2, env.region)


@task
@runs_once
def pricing(zone=env.azone):

    def average(x):
        return sum(x) * 1.0 / len(x)

    def variance(x):
        return average([y ** 2 for y in x]) - average(x) ** 2

    def stddev(x):
        return math.sqrt(variance(x))

    def median(x):
        return sorted(x)[len(x) // 2]

    now = datetime.datetime.now()
    one_day_ago = now - datetime.timedelta(days=1)
    price_history = env.ec2.describe_spot_price_history(
        StartTime=one_day_ago.isoformat(),
        EndTime=now.isoformat(),
        InstanceTypes=['g2.2xlarge'],
        ProductDescriptions=['Linux/UNIX'],
        AvailabilityZone=zone
    )

    print "AvailabilityZone : {}".format(zone)
    print "InstanceTypes : g2.2xlarge"

    prices = [float(x['SpotPrice']) for x in price_history['SpotPriceHistory']]
    latest_price = reduce(lambda y, x: x if x['Timestamp'] > y['Timestamp'] else y, price_history['SpotPriceHistory'])['SpotPrice']
    print 'Latest price : {}'.format(latest_price)
    print 'Daily average price : {}'.format(round(average(prices), 3))
    print 'Daily price standard deviation : {}'.format(round(stddev(prices), 3))
    print 'Daily price median : {}'.format(round(median(prices), 3))
    return


@task
@runs_once
def spot_ls(region=env.region):
    local('xdg-open https://{0}.console.aws.amazon.com/ec2sp/v1/spot/dashboard?region={0}'.format(region))


class SpotRequestResponse(object):

    @classmethod
    def create(cls, raw_response):
        return [cls(res) for res in raw_response['SpotInstanceRequests']]

    def __init__(self, response):
        self.request_id = response['SpotInstanceRequestId']
        self.state = response['State']
        self.status = response['Status']['Code']
        self.status_message = response['Status']['Message']
        self.instance_id = response.get('InstanceId', None)

    def __str__(self):
        return "SpotInstanceRequestId : {} State : {} Status : {} Message : {} InstanceId : {}".format(self.request_id,
                                                                                                       self.state,
                                                                                                       self.status,
                                                                                                       self.status_message,
                                                                                                       self.instance_id)


class SpotInstanceResponse(object):

    @classmethod
    def create(cls, raw_response):
        return [cls(res) for reservation in raw_response['Reservations'] for res in reservation['Instances']]

    def __init__(self, response):
        self.instance_id = response['InstanceId']
        self.state = response['State']['Name']
        self.public_ip = response.get('PublicIpAddress', None)

    def __str__(self):
        return "InstanceId : {} State : {} PublicIpAddress : {}".format(self.instance_id, self.state, self.public_ip)


def up_spot(spec, bid):
    response = env.ec2.request_spot_instances(SpotPrice=str(float(bid)),
                                              InstanceCount=1,
                                              LaunchSpecification=get_spec(spec))
    logging.info("Requested ec2 spot instances")
    logging.debug(response)
    request_repsonses = SpotRequestResponse.create(response)
    for resp in request_repsonses:
        logging.info(resp)

    return wait_for_spot_instances([req.request_id for req in request_repsonses])


def up_on_demand(spec):
    raise Exception("Not implemented yet")


def get_spec(spec_file):
    with open(spec_file, 'r') as sf:
        return json.load(sf)


def wait_for_spot_instances(request_ids):
    instance_ids = get_request_state(request_ids)
    instances = get_instance_status(instance_ids)
    get_instance_ssh_status([instance.public_ip for instance in instances])
    return instances


@with_retry(1)
def get_request_state(request_ids):
    logging.info('Get spot request status')
    response = env.ec2.describe_spot_instance_requests(SpotInstanceRequestIds=request_ids)
    request_repsonses = SpotRequestResponse.create(response)
    logging.debug(response)
    for resp in request_repsonses:
        logging.info(resp)
        if resp.status != 'fulfilled' or not resp.instance_id:
            raise Exception("Request wasn't fulfilled yet")
    return [resp.instance_id for resp in request_repsonses]


@with_retry(1)
def get_instance_status(instance_ids):
    logging.info('Get spot instance status')
    response = env.ec2.describe_instances(InstanceIds=instance_ids)
    request_responses = SpotInstanceResponse.create(response)
    logging.debug(response)
    for resp in request_responses:
        logging.info(resp)
        if resp.state != 'running' or not resp.public_ip:
            raise Exception("Instance isn't running yet")
    return request_responses


@with_retry(1)
def get_instance_ssh_status(ips):
    for ip in ips:
        with settings(hide('everything'), warn_only=True):
            result = local('nc -w 5 -zvv %s 22' % ip)
            if result.return_code != 0:
                raise Exception("Network port for {} isn't pingable yet".format(ip))

__all__ = ["up", "terminate", "ls", "pricing", "spot_ls", "regions", "zones"]
