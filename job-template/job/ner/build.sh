#!/bin/bash

set -ex

<<<<<<< HEAD
docker build -t ccr.ccs.tencentyun.com/cube-studio/ner:20220812 -f job/ner/Dockerfile .
=======
docker build -t ccr.ccs.tencentyun.com/cube-studio/ner:20220812 .
>>>>>>> 2b660f44b8ed04eef43742d5a85c5c31e1c0cefd
docker push ccr.ccs.tencentyun.com/cube-studio/ner:20220812



