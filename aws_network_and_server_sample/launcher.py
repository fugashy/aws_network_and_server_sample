# -*- coding: utf-8 -*-
import time

import boto3


class VpcLauncher():
    def __init__(self, client, conf: dict):
        self._conf = conf
        self._client = client
        self.info = None

    def run(self):
        self.info = self._client.create_vpc(
            CidrBlock=self._conf['CidrBlock'],
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['Name']}]}])

        self._client.modify_vpc_attribute(
            VpcId=self.info['Vpc']['VpcId'],
            EnableDnsHostnames={'Value': self._conf['EnableDnsHostnames']})

        print(f"create {self._conf['Name']}: {self.info['Vpc']['VpcId']}")

    def kill(self):
        if self.info is None:
            return

        self._client.delete_vpc(VpcId=self.info['Vpc']['VpcId'])
        print(f"delete {self._conf['Name']}: {self.info['Vpc']['VpcId']}")
        self.info = None


class SubnetLauncher():
    def __init__(
            self,
            client,
            conf: dict,
            vpc_by_name: dict):
        self._client = client
        self._conf = conf
        self._vpc_by_name = vpc_by_name
        self.info = None

    def run(self):
        self.info = self._client.create_subnet(
            AvailabilityZone=self._conf['AvailabilityZone'],
            CidrBlock=self._conf['CidrBlock'],
            VpcId=self._vpc_by_name[self._conf['vpc_name']].info['Vpc']['VpcId'],
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['Name']}]}])

        print(f"create {self._conf['Name']}: {self.info['Subnet']['SubnetId']}")

    def kill(self):
        if self.info is None:
            return

        self._client.delete_subnet(SubnetId=self.info['Subnet']['SubnetId'])
        print(f"delete {self._conf['Name']}: {self.info['Subnet']['SubnetId']}")


class InternetGateWayLauncher():
    def __init__(self, client, conf: dict, vpc_by_name):
        self._client = client
        self._conf = conf
        self._vpc_by_name = vpc_by_name
        self.info = None

    def run(self):
        self.info = self._client.create_internet_gateway()

        self._client.attach_internet_gateway(
            InternetGatewayId=self.info['InternetGateway']['InternetGatewayId'],
            VpcId=self._vpc_by_name[self._conf['vpc_name']].info['Vpc']['VpcId'])
        print(f"create {self._conf['Name']}: {self.info['InternetGateway']['InternetGatewayId']}")

    def kill(self):
        if self.info is None:
            return

        self._client.detach_internet_gateway(
            InternetGatewayId=self.info['InternetGateway']['InternetGatewayId'],
            VpcId=self._vpc_by_name[self._conf['vpc_name']].info['Vpc']['VpcId'])
        self._client.delete_internet_gateway(
            InternetGatewayId=self.info['InternetGateway']['InternetGatewayId'])
        print(f"delete {self._conf['Name']}: {self.info['InternetGateway']['InternetGatewayId']}")


class ElasticIpLauncher():
    def __init__(self, client, config):
        self._client = client
        self._conf = config
        self.info = None

    def run(self):
        self.info = self._client.allocate_address(Domain=self._conf['Domain'])
        print(f"create {self._conf['Name']}: {self.info['AllocationId']}")

    def kill(self):
        if self.info is None:
            return

        # NetworkInterfaceの情報を得て，アタッチされてないEIPをKill
        desc = self._client.describe_addresses(
            Filters=[{'Name': 'domain', 'Values': ['vpc']}])
        for rec in desc['Addresses']:
            if 'NetworkInterfaceId' not in rec:
                self._client.release_address(AllocationId=rec['AllocationId'])
        print(f"delete {self._conf['Name']}: {self.info['AllocationId']}")
        self.info = None


class RouteTableLauncher():
    def __init__(
            self,
            client,
            conf: dict,
            vpc_by_name: dict,
            subnet_by_name=None,
            igw_by_name=None,
            nat_by_name=None):
        self._client = client
        self._conf = conf
        self._vpc_by_name = vpc_by_name
        self._subnet_by_name = subnet_by_name
        self._igw_by_name = igw_by_name
        self._nat_by_name = nat_by_name
        self.info = None
        self._association_info = None
        self._route_info = list()

    def run(self):
        # VPCにルータを置くイメージ
        self.info = self._client.create_route_table(
            VpcId=self._vpc_by_name[self._conf['vpc_name']].info['Vpc']['VpcId'],
            TagSpecifications=[
                {
                    'ResourceType': 'route-table',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['Name']}]}])

        if 'subnet_name' in self._conf and self._subnet_by_name is not None:
            self._association_info = self._client.associate_route_table(
                RouteTableId=self.info['RouteTable']['RouteTableId'],
                SubnetId=self._subnet_by_name[self._conf['subnet_name']].info['Subnet']['SubnetId'])
        print(f"create {self._conf['Name']}: {self.info['RouteTable']['RouteTableId']}")

        for c in self._conf['routes']:
            # IGW, NATのうち，当てはまってるものがあればアタッチ
            # 微妙な実装になってしまった
            # 今後は素直にCloudFormationを使う
            if c['gw_name'] in self._igw_by_name:
                gateway_id = self._igw_by_name[c['gw_name']].info['InternetGateway']['InternetGatewayId']
            elif c['gw_name'] in self._nat_by_name:
                gateway_id = self._nat_by_name[c['gw_name']].info['NatGateway']['NatGatewayId']
            else:
                return
            self._route_info.append(self._client.create_route(
                DestinationCidrBlock=c['DestinationCidrBlock'],
                GatewayId=gateway_id,
                RouteTableId=self.info['RouteTable']['RouteTableId']))

    def kill(self):
        if len(self._route_info) != 0:
            for c in self._conf['routes']:
                self._client.delete_route(
                    DestinationCidrBlock=c['DestinationCidrBlock'],
                    RouteTableId=self.info['RouteTable']['RouteTableId'])

        if self._association_info is not None:
            self._client.disassociate_route_table(
                AssociationId=self._association_info['AssociationId'])

        if self.info is not None:
            self._client.delete_route_table(
                RouteTableId=self.info['RouteTable']['RouteTableId'])
        print(f"delete {self._conf['Name']}: {self.info['RouteTable']['RouteTableId']}")


class SecurityGroupLauncher():
    def __init__(self, client, conf, vpc_by_name):
        self._client = client
        self._conf = conf
        self._vpc_by_name = vpc_by_name
        self.info = dict()

    def run(self):
        self._conf['creation']['VpcId'] = self._vpc_by_name[self._conf['vpc_name']].info['Vpc']['VpcId']
        self.info['creation'] = self._client.create_security_group(**self._conf['creation'])

        ing_conf = self._conf['ingress']
        self.info['ingress'] = self._client.authorize_security_group_ingress(
            GroupId=self.info['creation']['GroupId'],
            IpPermissions=[
                {
                    'FromPort': pconf['FromPort'],
                    'IpProtocol': pconf['IpProtocol'],
                    'IpRanges': [{'CidrIp': pconf['CidrIp']}],
                    'Ipv6Ranges': [{
                        'CidrIpv6': pconf['CidrIpv6']}]
                    if 'CidrIpv6' in pconf else [],
                    'ToPort': pconf['ToPort']
                }
                for pconf in ing_conf['IpPermissions']
                ])

        if 'egress' in self._conf:
            eg_conf = self._conf['egress']
            self.info['egress'] = self._client.authorize_security_group_egress(
                GroupId=self.info['creation']['GroupId'],
                IpPermissions=[
                    {
                        'FromPort': pconf['FromPort'],
                        'IpProtocol': pconf['IpProtocol'],
                        'IpRanges': [{'CidrIp': pconf['CidrIp']}],
                        'Ipv6Ranges': [{
                            'CidrIpv6': pconf['CidrIpv6']}]
                        if 'CidrIpv6' in pconf else [],
                        'ToPort': pconf['ToPort']
                    }
                    for pconf in eg_conf['IpPermissions']
                    ])
        print(f"create {self._conf['creation']['GroupName']}: {self.info['creation']['GroupId']}")

    def kill(self):
        if len(self.info) <= 1:
            return

        self._client.delete_security_group(GroupId=self.info['creation']['GroupId'])
        print(f"delete {self._conf['creation']['GroupName']}: {self.info['creation']['GroupId']}")


class ElasticComputeCloudLauncher():
    def __init__(
            self,
            ec2_client,
            ec2_resource,
            conf,
            key_by_name,
            subnet_by_name,
            sg_by_name):
        self._client = ec2_client
        self._resource = ec2_resource
        self._conf = conf
        self._key_by_name = key_by_name
        self._subnet_by_name = subnet_by_name
        self._sg_by_name = sg_by_name
        self.instance = None
        self.info = None

    def run(self):
        self.instance = self._resource.create_instances(
            ImageId=self._conf['ImageId'],
            MinCount=self._conf['MinCount'],
            MaxCount=self._conf['MaxCount'],
            InstanceType=self._conf['InstanceType'],
            KeyName=self._conf['KeyName'],
            IamInstanceProfile=self._conf['IamInstanceProfile'],
            UserData=f'''
#!/bin/bash
{self._conf['UserData']}
            ''',
            NetworkInterfaces=[
                {
                    'AssociatePublicIpAddress': net_conf['AssociatePublicIpAddress'],
                    'DeleteOnTermination': net_conf['DeleteOnTermination'],
                    'DeviceIndex': net_conf['DeviceIndex'],
                    'Groups': [self._sg_by_name[self._conf['Groups']].info['creation']['GroupId']],
                    'SubnetId': self._subnet_by_name[self._conf['SubnetId']].info['Subnet']['SubnetId'],
                }
                for net_conf in self._conf['NetworkInterfaces']] if 'NetworkInterfaces' in self._conf else list(),
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['Name']}]}])[0]

        print(f'wait for ec2 running: {self.instance.instance_id}')
        self.instance.wait_until_running()
        self.info = self._resource.Instance(self.instance.instance_id)
        print(f"create {self._conf['Name']} ip: {self.info.public_ip_address}")

    def kill(self):
        if self.instance is None and self.info is None:
            return

        self._client.terminate_instances(InstanceIds=[self.instance.instance_id])
        print(f"wait for ec2 terminated: {self.instance.instance_id}")
        while self.instance.state['Name'] != 'terminated':
            time.sleep(1.0)
            self.instance.load()
        print(f"delete {self._conf['Name']} ip: {self.info.public_ip_address}")


class ElasticContainerServiceLauncher:
    def __init__(self, ecs_client, config):
        self._client = ecs_client
        self._conf = config
        self.info = dict()

        # clusterだけは先に作っておいたほうがいいような雰囲気してる
        self.info['cluster'] = self._client.create_cluster(
            clusterName=self._conf['create_cluster']['clusterName'],
            tags=[{
                'key': 'Name',
                'value': self._conf['create_cluster']['clusterName']}])
        print(f"create {self._conf['create_cluster']['clusterName']}")

        self.info['task'] = self._client.register_task_definition(
            **self._conf['task'])
        print(f"create {self.info['task']['taskDefinition']['taskDefinitionArn']}")

    def run(self):
        self.info['service'] = self._client.create_service(
            **self._conf['service'])
        print(f"create {self._conf['service']['serviceName']}")

    def kill(self):
        if len(self.info) == 0:
            return
        try:
            self._client.update_service(
                cluster=self._conf['create_cluster']['clusterName'],
                service=self._conf['service']['serviceName'],
                desiredCount=0)
            self._client.delete_service(
                cluster=self._conf['create_cluster']['clusterName'],
                service=self._conf['service']['serviceName'],
                force=True)
            print(f"delete {self._conf['service']['serviceName']}")
        except:
            print('service not found/not active')

        self._client.deregister_task_definition(
            taskDefinition=f"{self._conf['task']['family']}:{self.info['task']['taskDefinition']['revision']}")
        print(f"delete {self.info['task']['taskDefinition']['taskDefinitionArn']}")

        self._client.delete_cluster(
            cluster=f"{self._conf['create_cluster']['clusterName']}")
        print(f"delete {self._conf['create_cluster']['clusterName']}")


class NatGatewayLauncher():
    def __init__(self, client, config, subnet_by_name, eip_by_name):
        self._client = client
        self._conf = config
        self._subnet_by_name = subnet_by_name
        self._eip_by_name = eip_by_name
        self.info = None

    def run(self):
        self.info = self._client.create_nat_gateway(
            AllocationId=self._eip_by_name[self._conf['eip_name']].info['AllocationId'],
            SubnetId=self._subnet_by_name[self._conf['subnet_name']].info['Subnet']['SubnetId'])
        self._client.get_waiter('nat_gateway_available').wait(
            NatGatewayIds=[self.info['NatGateway']['NatGatewayId']])
        print(f"create {self._conf['Name']}: {self.info['NatGateway']['NatGatewayId']}")

    def kill(self):
        if self.info is None:
            return

        self._client.delete_nat_gateway(NatGatewayId=self.info['NatGateway']['NatGatewayId'])
        waiter = self._client.get_waiter('nat_gateway_available')
        waiter.wait(Filters=[
            {
                'Name': 'state',
                'Values': ['deleted']
            },{
                'Name': 'nat-gateway-id',
                'Values': [self.info['NatGateway']['NatGatewayId']]}])

        print(f"delete {self._conf['Name']}: {self.info['NatGateway']['NatGatewayId']}")
