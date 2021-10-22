# aws_network_and_server_sample

Construct Wordpress blog site on little secure VPC

- Launch all

- press enter to kill all of them

# 構成

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

# how to use

```bash
python aws_network_and_server_sample/main.py `pwd`/config/all.yaml
```

# 実行のためにやったこと（最小限というわけではないかもしれない）

- ecs-cliのインストール

  https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/ECS_CLI_installation.html
  https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/ECS_CLI_Configuration.html

- eclInstanceRoleの作成

- IAMの設定

# reference

- さわって学ぶクラウドインフラ Amazon Web Services 基礎からのネットワーク&サーバー構築

  日経BP

# web server

- dockerhubのPublic reposにあります

  ```bash
  docker pull fugashy/aws_web_server_sample:latest

  # 試運転
  docker run --rm -it --name web_server -p 80:80 aws_web_server_sample
  ```

# db server

- mariadbの公式イメージを用います

  ```bash
  docker pull mariadb

  # 試運転
  docker run -p 127.0.0.1:3306:3306 -e MARIADB_ROOT_PASSWORD=my-secret-pw -e MARIADB_DATABASE=wordpress --name db_server -it --rm mariadb
  ```
