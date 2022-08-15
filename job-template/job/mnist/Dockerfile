FROM pytorch/pytorch:0.4_cuda9_cudnn7

WORKDIR /workspace
RUN chmod -R a+w /workspace
ADD ./mnist_DDP.py /workspace/

ENTRYPOINT ["torchrun", "-u", "mnist_DDP.py", "--gpu"] 