# docker build -t csighub.tencentyun.com/tme-kubeflow/gpu:python3.6-cuda10.1-cuda10.0-cuda9.0-cudnn7.6 .


# 手动安装了各种cuda
# https://developer.nvidia.com/cuda-toolkit-archive
# FROM mirrors.tencent.com/star_library/g-tlinux2.2-python3.6-cuda10.1-cudnn7.6:latest
FROM csighub.tencentyun.com/tme-kubeflow/gpu:python3.6-cuda10.1-cuda10.0-cuda9.0-cudnn7.6-base

RUN rpm --rebuilddb && yum update -y &&  yum install -y --nogpgcheck gcc make gcc-c++ && yum clean all
RUN rpm --rebuilddb && yum groupinstall "fonts" -y --nogpgcheck && echo 'LANG="zh_CN.UTF-8"' > /etc/locale.conf  && source /etc/locale.conf

# RUN useradd user_00;echo "" | passwd  --stdin user_00
RUN mkdir -p /usr/local/services/ && mkdir -p /data/L5Backup/ && chmod -R 777 /data/L5Backup/
WORKDIR /usr/local/services/
RUN wget https://docker-76009.sz.gfp.tencent-cloud.com/tlinux/l5_protocol_32os-1.0.tar.gz && tar -zxvf l5_protocol_32os-1.0.tar.gz && rm l5_protocol_32os-1.0.tar.gz
#RUN wget https://docker-76009.sz.gfp.tencent-cloud.com/tlinux/dns_l5_agent-1.0.tar.gz && tar -zxvf dns_l5_agent-1.0.tar.gz && rm dns_l5_agent-1.0.tar.gz
RUN wget https://docker-76009.sz.gfp.tencent-cloud.com/tlinux/tdwdfs_client-1.0.tar.gz && tar -zxvf tdwdfs_client-1.0.tar.gz && rm tdwdfs_client-1.0.tar.gz
#RUN wget https://docker-76009.sz.gfp.tencent-cloud.com/tlinux/dc_agent-1.0.tar.gz && tar -zxvf dc_agent-1.0.tar.gz && rm dc_agent-1.0.tar.gz

WORKDIR /





