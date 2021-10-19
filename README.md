# aws_network_and_server_sample

Construct Wordpress blog site on little secure VPC

# reference

- さわって学ぶクラウドインフラ Amazon Web Services 基礎からのネットワーク&サーバー構築

  日経BP

# web server

- dockerhubにあります

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
