from ubuntu:20.04

arg DEBIAN_FRONTEND=noninteractive

# remove index.html to use index.php of wordpress
run apt-get update && \
  apt-get -y install apache2 php php-mysql wget && \
  rm -rf /var/www/html/index.html

run wget https://ja.wordpress.org/latest-ja.tar.gz && \
  tar xzvf latest-ja.tar.gz && \
  mv wordpress/* /var/www/html/ && \
  rm -rf wordpress latest-ja.tar.gz && \
  chown -R www-data:www-data /var/www/html

# envvars provides required values for apache2 like APACHE_RUN_DIR
run echo '. /etc/apache2/envvars' > /root/run_apache.sh && \
 echo 'mkdir -p /var/run/apache2' >> /root/run_apache.sh && \
 echo 'mkdir -p /var/lock/apache2' >> /root/run_apache.sh && \
 echo '/usr/sbin/apache2 -D FOREGROUND' >> /root/run_apache.sh && \
 chmod 755 /root/run_apache.sh

expose 80

cmd /root/run_apache.sh
