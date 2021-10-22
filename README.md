# aws_network_and_server_sample

Construct Wordpress blog site on little secure VPC

- Launch all

- press enter to kill all of them

# components after launch finished

  - VPC

    - Internet gateway

    - PublicSubnet

      - web_server container (ECS on EC2)

        Wordpress works

      - NAT Gateway with Elastic IP

      - PublicRootTable

    - PrivateSubnet

      - db_server container (ECS on EC2)

        MariaDB works

      - PrivateRootTable

# dependency

- python 3.7.4

- boto3 1.18.21

# required fee for AWS

- NAT and EIP(Creation and running)

  NAT is used for pulling docker image.

# required IAM roll for instance

- eclInstanceRole

# how to use

- launch

  ```bash
  python aws_network_and_server_sample/main.py `pwd`/config/all.yaml
  ```

- access to public IP of web_server_ec2 by your browser

  See stdout like create web_server_ec2: ip: xx.xxx.xxx.xx

- press enter to kill

# reference

- さわって学ぶクラウドインフラ Amazon Web Services 基礎からのネットワーク&サーバー構築

  日経BP

  https://www.amazon.co.jp/Amazon-Web-Services-基礎からのネットワーク＆サーバー構築-改訂3版-大澤-ebook/dp/B084QQ7TCF

# docker images for ECS

- web server

  - In public repos of dockerhub

    ```bash
    docker pull fugashy/aws_web_server_sample:latest

    # try
    docker run --rm -it --name web_server -p 80:80 aws_web_server_sample
    ```

- db server

  - use official mariadb

    ```bash
    docker pull mariadb

    # try
    docker run -p 127.0.0.1:3306:3306 -e MARIADB_ROOT_PASSWORD=my-secret-pw -e MARIADB_DATABASE=wordpress --name db_server -it --rm mariadb
    ```
