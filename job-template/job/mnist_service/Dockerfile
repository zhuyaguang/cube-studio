FROM pytorch/pytorch:1.12.1-cuda11.3-cudnn8-runtime


WORKDIR /workspace
RUN chmod -R a+w /workspace
ADD ./launcher.py /workspace/

ENTRYPOINT ["python3", "launcher.py"]