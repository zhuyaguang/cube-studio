FROM pytorch/pytorch:0.4_cuda9_cudnn7

WORKDIR /workspace
RUN chmod -R a+w /workspace
ADD ./launcher.py /workspace/

ENTRYPOINT ["python3", "launcher.py"]