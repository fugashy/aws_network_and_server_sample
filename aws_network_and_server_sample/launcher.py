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
