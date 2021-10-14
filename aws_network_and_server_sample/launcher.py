# -*- coding: utf-8 -*-
import boto3
import time


class VpcLauncher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self.id = None

    def run(self):
        res = self._client.create_vpc(
            CidrBlock=self._conf['CidrBlock'],
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['name']}]}])
        # keep id for termination
        self.id = res['Vpc']['VpcId']

        self._client.modify_vpc_attribute(
            VpcId=self.id,
            EnableDnsHostnames={'Value': self._conf['EnableDnsHostnames']})

        print(f"create {self._conf['name']}")

    def kill(self):
        if self.id is None:
            return

        self._client.delete_vpc(VpcId=self.id)
        self._id = None
        print(f"delete {self._conf['name']}")


class SubnetLauncher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self.id = None

    def run(self, attach_vpc_id):
        res = self._client.create_subnet(
            AvailabilityZone=self._conf['AvailabilityZone'],
            CidrBlock=self._conf['CidrBlock'],
            VpcId=attach_vpc_id,
            TagSpecifications=[
                {
                    'ResourceType': 'subnet',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['name']}]}])

        self.id = res['Subnet']['SubnetId']
        print(f"create {self._conf['name']}")

    def kill(self):
        if self.id is None:
            return

        self._client.delete_subnet(SubnetId=self.id)
        print(f"delete {self._conf['name']}")


class InternetGateWayLauncher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self.id = None
        self._attach_vpc_id = None

    def run(self, attach_vpc_id):
        res = self._client.create_internet_gateway()
        self.id = res['InternetGateway']['InternetGatewayId']

        self._client.attach_internet_gateway(
            InternetGatewayId=self.id, VpcId=attach_vpc_id)
        self._attach_vpc_id = attach_vpc_id
        print(f"create {self._conf['name']}")

    def kill(self):
        if self.id is None or self._attach_vpc_id is None:
            return

        self._client.detach_internet_gateway(
            InternetGatewayId=self.id, VpcId=self._attach_vpc_id)
        self._client.delete_internet_gateway(
            InternetGatewayId=self.id)
        print(f"delete {self._conf['name']}")


class RouteTableLauncher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self.id = None
        self._association_id = None

    def run(self, attach_vpc_id, *, attach_subnet_id=None):
        # VPCにルータを置くイメージ
        res = self._client.create_route_table(
            VpcId=attach_vpc_id,
            TagSpecifications=[
                {
                    'ResourceType': 'route-table',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['name']}]}])
        self.id = res['RouteTable']['RouteTableId']

        if attach_subnet_id is not None:
            res = self._client.associate_route_table(
                RouteTableId=self.id,
                SubnetId=attach_subnet_id)
            self._association_id = res['AssociationId']
        print(f"create {self._conf['name']}")

    def kill(self):
        if self.id is None:
            return

        if self._association_id is not None:
            self._client.disassociate_route_table(
                AssociationId=self._association_id)

        self._client.delete_route_table(RouteTableId=self.id)
        print(f"delete {self._conf['name']}")


class RouteLauncher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self.id = None
        self._rt_id = None

    def run(self, attach_rt_id, *, attach_igw_id=None):
        # igwへのトラフィックを設定し，テーブルに登録
        self._client.create_route(
            DestinationCidrBlock=self._conf['DestinationCidrBlock'],
            GatewayId=attach_igw_id,
            RouteTableId=attach_rt_id)
        self._rt_id = attach_rt_id

    def kill(self):
        if self.id is None:
            return

        self._client.delete_route(
            DestinationCidrBlock=self._conf['DestinationCidrBlock'],
            RouteTableId=self._rt_id)


class SecurityGroupLauncher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self.id = None

    def run(self, vpc_id):
        res = self._client.create_security_group(
            Description=self._conf['Description'],
            GroupName=self._conf['GroupName'],
            VpcId=vpc_id,
            TagSpecifications=[
                {
                    'ResourceType': 'security-group',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['GroupName']}]}])
        self.id = res['GroupId']
        print(f"create {self._conf['GroupName']}")

        self._client.authorize_security_group_ingress(
            GroupId=self.id,
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
                for pconf in self._conf['IpPermissions']
                ])

    def kill(self):
        if self.id is None:
            return

        self._client.delete_security_group(
            GroupId=self.id)
        print(f"delete {self._conf['GroupName']}")


class ElasticComputeCloudLauncher():
    def __init__(self, conf: dict):
        self._conf = conf

        self._client = boto3.resource('ec2')
        self.id = None
        self.ip = None

        self._instance = None

    def run(self, key_name, subnet_id, sg_id):
        self._instance = self._client.create_instances(
            ImageId=self._conf['ImageId'],
            MinCount=self._conf['MinCount'],
            MaxCount=self._conf['MaxCount'],
            InstanceType=self._conf['InstanceType'],
            KeyName=key_name,
#           SecurityGroupIds=[sg_id],
#           SubnetId=subnet_id,
            NetworkInterfaces=[
                {
                    'AssociatePublicIpAddress': net_conf['AssociatePublicIpAddress'],
                    'DeleteOnTermination': net_conf['DeleteOnTermination'],
                    'DeviceIndex': net_conf['DeviceIndex'],
                    'Groups': [sg_id],
                    'SubnetId': subnet_id,
                }
                for net_conf in self._conf['NetworkInterfaces']],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': self._conf['Name']}]}])[0]

        self.id = self._instance.instance_id
        print(f'wait for ec2 running: {self.id}')
        self._instance.wait_until_running()
        self.ip = self._client.Instance(self.id).public_ip_address
        print(f"create {self._conf['Name']} ip: {self.ip}")

    def kill(self):
        if self.id is None and self.ip is None and self._instance is None:
            return

        c = boto3.client('ec2')
        c.terminate_instances(InstanceIds=[self.id])
        print(f"wait for ec2 terminated: {self.id}")
        while self._instance.state['Name'] != 'terminated':
            time.sleep(1.0)
            self._instance.load()
        print(f"delete {self._conf['Name']} ip: {self.ip}")
