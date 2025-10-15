# 取到使用当前目录下的编排文件启动的服务容器id  
previous_container=`docker-compose ps -q backend`

# 将容器数量调度到指定值，此值需要大于当前服务的容器数量  
docker-compose up -d --build --no-deps --scale backend=2 --no-recreate

sleep 5

# 杀掉标识的旧容器  
docker kill $previous_container

sleep 2

# 清理杀掉的旧容器
docker rm -f $previous_container

# 将新服务调度到指定数量
docker-compose up -d --no-deps --scale backend=2 --no-recreate