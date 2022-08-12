#!/bin/bash

set -ex

docker build -t ccr.ccs.tencentyun.com/cube-studio/download-minio:20220812 -f job/download_minio/Dockerfile .
docker push ccr.ccs.tencentyun.com/cube-studio/download-minio:20220812



