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
        print(f"create {self._conf['name']}")

    def kill(self):
        if self.id is None:
            return

        self._client.delete_vpc(VpcId=self.id)
        print(f"delete {self._conf['name']}")


class SubnetLauncher():
    def __init__(self, conf, attach_vpc_id):

        self._ids['subnets'] = dict()
        for subnet_conf in self._conf['subnets']:
            private_subnet = self._client.create_subnet(
                CidrBlock=subnet_conf['CidrBlock'],
                VpcId=self._ids[vpc_conf['name']],
                TagSpecifications=[
                    {
                        'ResourceType': 'subnet',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': subnet_conf['name']}]}])

            self._ids['subnets'][subnet_conf['name']] = private_subnet['Subnet']['SubnetId']

            print(f"create {subnet_conf['name']}")


        pass

    def kill(self):
        print('kill')



        for subnet_id in self._ids['subnets'].keys():
            pass


        pass
