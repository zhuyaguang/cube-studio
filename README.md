# Cube Studio

### 整体架构


![image](https://user-images.githubusercontent.com/20157705/167534673-322f4784-e240-451e-875e-ada57f121418.png)

cube是tme开源的一站式云原生机器学习平台，目前主要包含
 - 1、数据管理：特征平台，支持在/离线特征；数据源管理，支持结构数据和媒体标注数据管理；
 - 2、在线开发：在线的vscode/jupyter代码开发；在线镜像调试，支持免dockerfile，增量构建；
 - 3、训练编排：任务流编排，在线拖拉拽；开放的模板市场，支持tf/pytorch/mxnet/spark/ray/horovod/kaldi/volcano等分布式计算/训练任务；task的单节点debug，分布式任务的批量优先级调度，聚合日志；任务运行资源监控，报警；定时调度，支持补录，忽略，重试，依赖，并发限制，定时任务算力的智能修正；
 - 4、超参搜索：nni，katib，ray的超参搜索；
 - 5、推理服务：tf/pytorch/onnx模型的推理服务，serverless流量管控，triton gpu推理加速，依据gpu利用率/qps等指标的hpa能力，虚拟化gpu，虚拟显存等服务化能力；
 - 6、资源统筹：多集群多项目组资源统筹，联邦调度，边缘计算；

# 帮助文档

https://github.com/tencentmusic/cube-studio/wiki

# 开源共建

 学习、部署、体验、开源建设 欢迎来撩。或添加微信luanpeng1234，备注<开源建设>， [共建指南](https://github.com/tencentmusic/cube-studio/wiki/%E5%85%B1%E5%BB%BA%E6%8C%87%E5%8D%97)

<img border="0" width="20%" src="https://luanpeng.oss-cn-qingdao.aliyuncs.com/github/wechat.jpg" />
 
 
# 支持模板

提示：
- 1、能单机运行没必要多机运行  
- 2、开发自定义模板，更符合自己业务线下的需求

| 模板  | 类型 | 组件说明 |
| :----- | :---- | :---- |
| 自定义镜像 | 单机 | 完全自定义单机运行环境，可自由实现所有自定义单机功能 | 
| datax | 单机 | 异构数据源导入导出 | 
| xgb | 单机 | xgb模型训练 |
| deploy-service | 单机 | 部署云原生推理服务 | 
| ray | 分布式 | python ray框架 多机分布式功能，适用于超多文件在多机上的并发处理 |
| ray-sklearn | 分布式 | 基于ray框架的sklearn支持算法多机分布式并行计算  |
| volcano | 分布式 | volcano框架的多机分布式，可紫玉控制代码，利用环境变量实现多机worker的工作与协同  | 
| pytorchjob-train | 分布式 | 	pytorch的多机多卡分布式训练  | 
| media-download | 分布式 | 	分布式媒体文件下载  | 
| video-audio | 分布式 | 	分布式视频提取音频  | 
| video-img | 分布式 | 	分布式视频提取图片  | 
| model-offline-predict | 分布式 | 	分布式模型离线推理  | 
| tfjob-train | 分布式 | tf分布式训练，内部支持plain和runner两种方式  | 
| tfjob-runner | 分布式 | tf分布式-runner方式  | 
| tfjob-plain | 分布式 | tf分布式-plain方式  | 
| tf-distribute-model-evaluation | 分布式 | tensorflow2.3分布式模型评估  | 
| tf-model-offline-predict | 分布式 | tf模型离线推理  | 
| kaldi-distributed-on-volcanojob | 分布式 | kaldi音频分布式训练  | 

 
# 平台部署

[参考wiki](https://github.com/tencentmusic/cube-studio/wiki/%E5%B9%B3%E5%8F%B0%E5%8D%95%E6%9C%BA%E9%83%A8%E7%BD%B2)

平台完成部署之后如下:

<img width="100%" alt="167874734-5b1629e0-c3bb-41b0-871d-ffa43d914066" src="https://user-images.githubusercontent.com/20157705/168214806-b8aceb3d-e1b4-48f0-a079-903ef8751f40.png">

# 体验环境

[http://159.75.208.175/](http://81.69.195.6/)

# 贡献
 
@jaffe-fly <img width="5%" src="https://avatars.githubusercontent.com/u/49515380?s=96&v=4" />
@ma-chengcheng<img width="5%" src="https://avatars.githubusercontent.com/u/15444349?s=96&v=4" />
@chendile <img width="5%" src="https://avatars.githubusercontent.com/u/42484658?s=96&v=4" />
@xiaoyangmai <img width="5%" src="https://avatars.githubusercontent.com/u/10969390?s=96&v=4" />
@VincentWei2021 <img width="5%" src="https://avatars.githubusercontent.com/u/77832074?v=4" />
@SeibertronSS <img width="5%" src="https://avatars.githubusercontent.com/u/69496864?v=4" />
@cyxnzb <img width="5%" src="https://avatars.githubusercontent.com/u/51886383?s=88&v=4" /> 
@gilearn <img width="5%" src="https://avatars.githubusercontent.com/u/107160156?s=88&v=4" />
 

# 合作公司

![图片 1](https://user-images.githubusercontent.com/20157705/174600451-2fe38ff1-ff78-4bc8-bc63-2a6f5246e0af.png)
