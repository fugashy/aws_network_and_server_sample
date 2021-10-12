#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import yaml

from launcher import Launcher


@click.command()
@click.argument('vpc_config_file', type=str)
def main(vpc_config_file):
    f = open(vpc_config_file)
    config = yaml.safe_load(f)

    l = Launcher(config)

    try:
        l.run()
    except Exception as e:
        print(f'Error: {e}')

    input('Enter to terminate instances')

    l.kill()


if __name__ == '__main__':
    main()

