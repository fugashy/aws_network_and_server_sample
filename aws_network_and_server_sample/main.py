#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import yaml

from launcher import (
    SubnetLauncher,
    VpcLauncher,
)


@click.command()
@click.argument('config_file', type=str)
def main(config_file):
    f = open(config_file)
    config = yaml.safe_load(f)

    vpc_array = [VpcLauncher(c) for c in config['vpc']]
    subnet_array = [SubnetLauncher(c) for c in config['subnet']]

    try:
        [vpc.run() for vpc in vpc_array]
        vpc_id = vpc_array[0].id
        [subnet.run(vpc_id) for subnet in subnet_array]
    except Exception as e:
        print(f'Error: {e}')

    input('Enter to terminate instances')

    [subnet.kill() for subnet in reversed(subnet_array)]
    [vpc.kill() for vpc in reversed(vpc_array)]


if __name__ == '__main__':
    main()

