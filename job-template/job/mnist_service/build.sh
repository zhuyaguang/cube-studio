#!/bin/bash

set -ex

docker build -t ccr.ccs.tencentyun.com/cube-studio/mnist-svc:20220817 -f job/mnist_service/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/mnist-svc:20220817



