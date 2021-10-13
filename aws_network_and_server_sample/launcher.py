# -*- coding: utf-8 -*-
import boto3


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
