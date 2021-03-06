# -*- coding: utf-8 -*-
import os

import boto3


class KeyGenerator():
    def __init__(self, client, conf: dict):
        self._client = client
        self._conf = conf
        if self._conf['save_dir_path'][-1] != '/':
            self._conf['save_dir_path'] += '/'
        self.info = None

    def gen(self) -> str:
        try:
            self.info = self._client.create_key_pair(
                KeyName=self._conf['name'])
        except Exception as e:
            info = self._client.describe_key_pairs(
                KeyNames=[self._conf['name']])
            self._client.delete_key_pair(
                KeyName=info['KeyPairs'][0]['KeyName'],
                KeyPairId=info['KeyPairs'][0]['KeyPairId'])
            raise RuntimeError('Duplecated key error: try again')

        meta_data = self.info['KeyMaterial']
        key_file_name = f"{self._conf['name']}.pem"

        key_path = f"{self._conf['save_dir_path']}{key_file_name}"

        try:
            os.remove(key_path)
        except:
            pass
        os.umask(0)
        with open(key_path, mode='w', opener=lambda path, flags: os.open(path, flags, 0o400)) as f:
            f.write(meta_data)

        return key_path

    def delete(self):
        self._client.delete_key_pair(
            KeyName=self.info['KeyName'],
            KeyPairId=self.info['KeyPairId'])
