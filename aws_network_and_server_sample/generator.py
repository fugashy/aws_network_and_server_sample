# -*- coding: utf-8 -*-
import boto3


class KeyGenerator():
    def __init__(self, conf: dict):
        self._conf = conf
        if self._conf['save_dir_path'][-1] != '/':
            self._conf['save_dir_path'] += '/'

        self._client = boto3.client('ec2')

        self._key_pair = self._client.create_key_pair(
            KeyName=self._conf['key_name'])

    def gen(self) -> str:
        meta_data = self._key_pair['KeyMaterial']
        key_file_name = f"{self._conf['key_name']}.pem"


        key_path = f"{self._conf['save_dir_path']}{key_file_name}"

        with open(key_path, mode='w') as f:
            f.write(meta_data)

        return key_path

    def delete(self):
        self._client.delete_key_pair(
            KeyName=self._key_pair['KeyName'],
            KeyPairId=self._key_pair['KeyPairId'])
