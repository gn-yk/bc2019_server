# Bootcamp2019 Server研修

### 起動方法
1. `git clone git@github.com:gn-yk/bc2019_server.git`

2. `cd bc2019_server.git`

3. `docker-compose up`

+ localhostの5000番ポートにredisサーバが立ち上がります
  + テスト用: `redis-cli -h localhost -p 5000 PING`