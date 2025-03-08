#### Installation de rabbitmq

- brew install rabbitmq
- export PATH=$PATH:/usr/local/opt/rabbitmq/sbin
- brew services start rabbitmq

#### creation d'un serveur SMTP localement

- python -m smtpd -c DebuggingServer -n 0.0.0.0:1025
