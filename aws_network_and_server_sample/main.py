#!/usr/bin/env python
# -*- coding: utf-8 -*-
import click
import yaml

from launcher import (
    InternetGateWayLauncher,
    RouteLauncher,
    RouteTableLauncher,
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
    igw_array = [InternetGateWayLauncher(c) for c in config['internet_gateway']]
    rt_array = [RouteTableLauncher(c) for c in config['route_table']]
    route_array = [RouteLauncher(c) for c in config['route']]

    try:
        # TODO(fugashy) この辺のデータ受け渡し方法は微妙だが，
        # - AWSの仕様を完全に把握していないので下手に抽象化などは避けた
        # - 本の内容を掴むには十分
        # なのでしばらくこのまま
        [vpc.run() for vpc in vpc_array]
        vpc_id = vpc_array[0].id
        [subnet.run(vpc_id) for subnet in subnet_array]
        # publicな方はルートテーブルを設定するのでID確保
        public_subnet_id = subnet_array[0].id
        [igw.run(vpc_id) for igw in igw_array]
        # IGWのIDはルートテーブル設定に必要なので確保
        igw_id = igw_array[0].id
        [rt.run(vpc_id, attach_subnet_id=public_subnet_id) for rt in rt_array]
        rt_id = rt_array[0].id
        [route.run(rt_id, attach_igw_id=igw_id) for route in route_array]
    except Exception as e:
        print(f'Error: {e}')

    input('Enter to terminate instances')

    [route.kill() for route in reversed(route_array)]
    [rt.kill() for rt in reversed(rt_array)]
    [igw.kill() for igw in reversed(igw_array)]
    [subnet.kill() for subnet in reversed(subnet_array)]
    [vpc.kill() for vpc in reversed(vpc_array)]


if __name__ == '__main__':
    main()

