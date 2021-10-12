# -*- coding: utf-8 -*-
import boto3


class Launcher():
    def __init__(self, conf):
        self._conf = conf

        self._client = boto3.client('ec2')
        self._ids = dict()

    def run(self):
        print('run')

        vpc_conf = self._conf['vpc']
        vpc_res = self._client.create_vpc(
            CidrBlock=vpc_conf['CidrBlock'],
            TagSpecifications=[
                {
                    'ResourceType': 'vpc',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': vpc_conf['name']}]}])
        # keep id for termination
        self._ids['vpc'] = dict()
        self._ids['vpc'][vpc_conf['name']] = vpc_res['Vpc']['VpcId']
        print(f"create {vpc_conf['name']}")

#       self._ids['subnets'] = dict()
#       for subnet_conf in self._conf['subnets']:
#           private_subnet = self._client.create_subnet(
#               CidrBlock=subnet_conf['CidrBlock'],
#               VpcId=self._ids[vpc_conf['name']],
#               TagSpecifications=[
#                   {
#                       'ResourceType': 'subnet',
#                       'Tags': [
#                           {
#                               'Key': 'Name',
#                               'Value': subnet_conf['name']}]}])
#
#           self._ids['subnets'][subnet_conf['name']] = private_subnet['Subnet']['SubnetId']
#
#           print(f"create {subnet_conf['name']}")


        pass

    def kill(self):
        print('kill')

        if len(self._ids) == 0:
            return


#       for subnet_id in self._ids['subnets'].keys():
#           pass

        self._client.delete_vpc(VpcId=self._ids['vpc'][self._conf['vpc']['name']])
        print(f"delete {self._conf['vpc']['name']}")

        pass
