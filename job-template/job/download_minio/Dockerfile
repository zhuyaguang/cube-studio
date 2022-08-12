FROM python:3.7

RUN python3 -m pip install minio

LABEL maintainer "zhuyaguang <zhuyaguang@zhejianglab.com>"

COPY ./download-data.py .

ENTRYPOINT ["python3", "launcher.py"]


