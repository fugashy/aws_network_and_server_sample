#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import traceback
import yaml

import boto3

from generator import (
    KeyGenerator,
)
from launcher import (
    ElasticComputeCloudLauncher,
    ElasticContainerServiceLauncher,
    ElasticIpLauncher,
    InternetGateWayLauncher,
    NatGatewayLauncher,
    RouteTableLauncher,
    SecurityGroupLauncher,
    SubnetLauncher,
    VpcLauncher,
)


@click.command()
@click.argument('config_file', type=str)
def main(config_file):
    f = open(config_file)
    config = yaml.safe_load(f)

    ec2_client = boto3.client('ec2')
    ec2_resource = boto3.resource('ec2')
    ecs_client = boto3.client('ecs')

    # Key Pair
    key_by_name = {c['name']: KeyGenerator(ec2_client, c) for c in config['key']}
    key_path_array = [key_by_name[name].gen() for name in key_by_name.keys()]

    try:
        # VPC
        vpc_by_name = {
            c['Name']: VpcLauncher(ec2_client, c)
            for c in config['vpc']}
        [vpc_by_name[name].run() for name in vpc_by_name.keys()]
        # Subnet
        subnet_by_name = {
            c['Name']: SubnetLauncher(ec2_client, c, vpc_by_name)
            for c in config['subnet']}
        [subnet_by_name[name].run() for name in subnet_by_name.keys()]
        # Internet Gateway
        igw_by_name = {
            c['Name']: InternetGateWayLauncher(ec2_client, c, vpc_by_name)
            for c in config['internet_gateway']}
        [igw_by_name[name].run() for name in igw_by_name.keys()]
        # Elastic IP
        eip_by_name = {
            c['Name']: ElasticIpLauncher(ec2_client, c)
            for c in config['elastic_ip']}
        [eip_by_name[name].run() for name in eip_by_name.keys()]
        # NAT Gateway
        nat_by_name = {
            c['Name']: NatGatewayLauncher(ec2_client, c, subnet_by_name, eip_by_name)
            for c in config['nat_gateway']}
        [nat_by_name[name].run() for name in nat_by_name.keys()]
        # Route Table
        rt_by_name = {
            c['Name']: RouteTableLauncher(ec2_client, c, vpc_by_name, subnet_by_name, igw_by_name, nat_by_name)
            for c in config['route_table']}
        [rt_by_name[name].run() for name in rt_by_name.keys()]
        # Security Group
        sg_by_name = {
            c['creation']['GroupName']: SecurityGroupLauncher(ec2_client, c, vpc_by_name)
            for c in config['security_group']}
        [sg_by_name[name].run() for name in sg_by_name.keys()]
        # Elastic Container Service
        ecs_by_name = {
            c['create_cluster']['clusterName']: ElasticContainerServiceLauncher(ecs_client, c)
            for c in config['elastic_container_service']}
        # Elastic Compute Cloud
        ec2_by_name = {
            c['Name']: ElasticComputeCloudLauncher(
                ec2_client, ec2_resource, c, key_by_name, subnet_by_name, sg_by_name)
            for c in config['elastic_compute_cloud']}
        [ec2_by_name[name].run() for name in ec2_by_name.keys()]
        [ecs_by_name[name].run() for name in ecs_by_name.keys()]

        input('Enter to terminate instances')
    except:
        traceback.print_exc()

    try:
        # ??????EC2???Kill???????????????????????????
        [ec2_by_name[name].kill() for name in reversed(sorted(ec2_by_name.keys()))]
        [ecs_by_name[name].kill() for name in reversed(sorted(ecs_by_name.keys()))]
        [key_by_name[name].delete() for name in reversed(sorted(key_by_name.keys()))]
        [sg_by_name[name].kill() for name in reversed(sorted(sg_by_name.keys()))]
        [rt_by_name[name].kill() for name in reversed(sorted(rt_by_name.keys()))]
        [nat_by_name[name].kill() for name in reversed(sorted(nat_by_name.keys()))]
    except Exception as e:
        print(e)
    [eip_by_name[name].kill() for name in reversed(sorted(eip_by_name.keys()))]
    [igw_by_name[name].kill() for name in reversed(sorted(igw_by_name.keys()))]
    [subnet_by_name[name].kill() for name in reversed(sorted(subnet_by_name.keys()))]
    [vpc_by_name[name].kill() for name in reversed(sorted(vpc_by_name.keys()))]


if __name__ == '__main__':
    main()
