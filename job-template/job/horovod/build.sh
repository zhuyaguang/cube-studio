#!/bin/bash

set -ex
docker build -t csighub.tencentyun.com/tme-kubeflow/horovod:cpu-20210401 -f job/horovod/Dockerfile-cpu .
docker push csighub.tencentyun.com/tme-kubeflow/horovod:cpu-20210401

#docker build -t csighub.tencentyun.com/tme-kubeflow/horovod:gpu-20210401 -f job/horovod/Dockerfile-gpu .
#docker push csighub.tencentyun.com/tme-kubeflow/horovod:gpu-20210401





