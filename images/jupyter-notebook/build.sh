set -ex
hubhost=ccr.ccs.tencentyun.com/cube-studio
base_image=ubuntu:18.04
docker build -t $hubhost/notebook:jupyter-ubuntu-cpu-base --build-arg FROM_IMAGES=$base_image -f Dockerfile-ubuntu-base .
docker push $hubhost/notebook:jupyter-ubuntu-cpu-base

# 构建hadoop镜像
docker build -t  $hubhost/notebook:jupyter-ubuntu-cpu-hadoop -f hadoop/Dockerfile-ubuntu-hadoop .
docker push $hubhost/notebook:jupyter-ubuntu-cpu-hadoop


base_image=nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04
docker build -t $hubhost/notebook:jupyter-ubuntu-gpu-base --build-arg FROM_IMAGES=$base_image -f Dockerfile-ubuntu-base .
docker push $hubhost/notebook:jupyter-ubuntu-gpu-base