#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import yaml

from launcher import VpcLauncher


@click.command()
@click.argument('config_file', type=str)
def main(config_file):
    f = open(config_file)
    config = yaml.safe_load(f)

    vpc_array = [VpcLauncher(c) for c in config['vpc']]

    try:
        [vpc.run() for vpc in vpc_array]
    except Exception as e:
        print(f'Error: {e}')

    input('Enter to terminate instances')

    [vpc.kill() for vpc in reversed(vpc_array)]


if __name__ == '__main__':
    main()

