#!/bin/bash

set -ex

docker build -t ccr.ccs.tencentyun.com/cube-studio/mnist:20211001 -f job/mnist/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/mnist:20220814



