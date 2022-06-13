# FROM ubuntu:18.04
FROM nvidia/cuda:11.5.0-cudnn8-runtime-ubuntu20.04

ENV TENSORFLOW_VERSION=2.3.0
ENV PYTORCH_VERSION=1.6.0
ENV TORCHVISION_VERSION=0.7.0
ENV MXNET_VERSION=1.5.0
ENV HOROVOD_VERSION=0.24.3

# Python 2.7 or 3.6 is supported by Ubuntu Bionic out of the box
ARG python=3.8
ENV PYTHON_VERSION=${python}

# Set default shell to /bin/bash
SHELL ["/bin/bash", "-cu"]

RUN apt-get update && apt-get install -y --allow-downgrades --allow-change-held-packages --no-install-recommends \
        build-essential \
        cmake \
        g++-5 \
        git \
        curl \
        vim \
        wget \
        ca-certificates \
        libjpeg-dev \
        libpng-dev \
        python${PYTHON_VERSION} \
        python${PYTHON_VERSION}-dev \
        librdmacm1 \
        libibverbs1 \
        ibverbs-providers

RUN if [[ "${PYTHON_VERSION}" == "3.6" ]]; then \
        apt-get install -y python${PYTHON_VERSION}-distutils; \
    fi

RUN ln -s /usr/bin/python${PYTHON_VERSION} /usr/bin/python

RUN if [[ "${PYTHON_VERSION}" == "3.6" ]]; then \
        curl -O https://bootstrap.pypa.io/pip/3.6/get-pip.py && \
        python get-pip.py && \
        rm get-pip.py; \
    else \
        curl -O https://bootstrap.pypa.io/get-pip.py && \
        python get-pip.py && \
        rm get-pip.py; \
    fi


# Install TensorFlow, Keras, PyTorch and MXNet
RUN pip install future typing
RUN pip install numpy \
        tensorflow==${TENSORFLOW_VERSION} \
        keras \
        h5py
RUN pip install torch==${PYTORCH_VERSION} torchvision==${TORCHVISION_VERSION}
RUN pip install mxnet==${MXNET_VERSION}

# Install Open MPI
RUN mkdir /tmp/openmpi && \
    cd /tmp/openmpi && \
    wget https://www.open-mpi.org/software/ompi/v4.0/downloads/openmpi-4.0.0.tar.gz && \
    tar zxf openmpi-4.0.0.tar.gz && \
    cd openmpi-4.0.0 && \
    ./configure --enable-orterun-prefix-by-default && \
    make -j $(nproc) all && \
    make install && \
    ldconfig && \
    rm -rf /tmp/openmpi

# Install OpenSSH for MPI to communicate between containers
RUN apt-get install -y --no-install-recommends openssh-client openssh-server && \
    mkdir -p /var/run/sshd

# Allow OpenSSH to talk to containers without asking for confirmation
RUN cat /etc/ssh/ssh_config | grep -v StrictHostKeyChecking > /etc/ssh/ssh_config.new && \
    echo "    StrictHostKeyChecking no" >> /etc/ssh/ssh_config.new && \
    mv /etc/ssh/ssh_config.new /etc/ssh/ssh_config && mkdir /examples

## Install Horovod
RUN HOROVOD_CPU_OPERATIONS=MPI HOROVOD_WITH_TENSORFLOW=1 HOROVOD_WITH_PYTORCH=1 HOROVOD_WITH_MXNET=1 \
    pip install --no-cache-dir horovod==${HOROVOD_VERSION}

RUN pip install pysnooper dill requests kubernetes

# Get example python scripts
COPY job/horovod/demo/* /examples/

WORKDIR /examples

ENTRYPOINT ["python", "start.py"]


# docker run --name horovod -it --entrypoint '' ccr.ccs.tencentyun.com/cube-studio/mpi:horovod-20210401 bash