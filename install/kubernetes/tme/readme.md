# kubernetes部署

## 部署元数据组件mysql （可用cdb），已部署可忽略

## 部署缓存组件redis (ckv plus部分功能不支持)，已部署可忽略

## 部署configmap.yaml

kubectl delete configmap kubeflow-dashboard-config -n infra
kubectl create configmap kubeflow-dashboard-config --from-file=config -n infra

kubectl delete configmap kubernetes-config -n infra
kubectl create configmap kubernetes-config --from-file=kubeconfig -n infra

kubectl delete configmap kubernetes-config -n pipeline
kubectl create configmap kubernetes-config --from-file=kubeconfig -n pipeline

kubectl delete configmap kubernetes-config -n katib
kubectl create configmap kubernetes-config --from-file=kubeconfig -n katib


包含
entrypoint.sh 镜像启动脚本
config.py  配置文件，需要将其中的配置项替换为自己的

## 部署pv-pvc.yaml

在myapp高可用时需要使用分布式存储在存放下载文件。所以需要使用pv/pvc，可根据自己的实际情况部署pv。


## 部署 deploy.yaml
deploy.yaml为myapp的前后端代码
在部署文件中需要修改成自己的环境变量



