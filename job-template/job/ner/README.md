# ner 模板

## 模版简介
  命名实体识别（NER）是一种自然语言处理技术，可以自动扫描整篇文章，提取文本中的一些基本实体，并将它们分类到预定义的类别中。
  举一个直观一点的例子，比如你对手机的语音助手说，“提醒我明天下午7点开会”，或者“明天北京海淀区的天气怎么样”，然后它就会根据你的指令来做出相应的执行。
  主要应用于：搜索和推荐引擎、自动聊天机器人、内容分析、消费者洞察
## 使用说明

1. 训练镜像打包，并添加到 cube-studio

   `docker build -t ccr.ccs.tencentyun.com/cube-studio/ner:20220812 -f Dockerfile .`
   `docker push ccr.ccs.tencentyun.com/cube-studio/ner:20220812`

   ![image-20220819133248945](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819133248945.png)

2. 服务镜像打包，并添加到 cube-studio

   进入到 `job-template/job/ner_service` 目录

   `docker build -t ccr.ccs.tencentyun.com/cube-studio/ner-service:20220812 -f Dockerfile .`

   `docker push ccr.ccs.tencentyun.com/cube-studio/ner-service:20220812`

   ![image-20220819133355090](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819133355090.png)

3. 准备数据集

   数据集 可以通过[链接]()下载

   把数据拷贝到 note book 中 `/mnt/admin/NER` 目录（可以直接拖拽进去）

   ![image-20220819133738821](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819133738821.png)

4. 集成到 cube-studio 平台

   * 添加 训练模版，填写镜像和启动参数

     ![image-20220819134710025](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819134710025.png)

   * 启动参数，可以复制下面

   ```json
   {
       "参数分组1": {
           "--model": {
               "type": "str",
               "item_type": "str",
               "label": "参数1",
               "require": 1,
               "choice": [],
               "range": "",
               "default": "BiLSTM_CRF",
               "placeholder": "",
               "describe": "model",
               "editable": 1,
               "condition": "",
               "sub_args": {}
           },
           "--objectname": {
               "type": "str",
               "item_type": "str",
               "label": "参数2",
               "require": 1,
               "choice": [
                   "resume_BIO.txt",
                   "people_daily_BIO.txt"
               ],
               "range": "",
               "default": "resume_BIO.txt",
               "placeholder": "",
               "describe": "resume_BIO",
               "editable": 1,
               "condition": "",
               "sub_args": {}
           },
           "--epochs": {
               "type": "int",
               "item_type": "str",
               "label": "参数3",
               "require": 1,
               "choice": [],
               "range": "",
               "default": "5",
               "placeholder": "",
               "describe": "epochs",
               "editable": 1,
               "condition": "",
               "sub_args": {}
           },
           "--path": {
               "type": "str",
               "item_type": "str",
               "label": "参数4",
               "require": 1,
               "choice": [],
               "range": "",
               "default": "/mnt/admin/NER/zdata/",
               "placeholder": "",
               "describe": "数据集地址",
               "editable": 1,
               "condition": "",
               "sub_args": {}
           },
           "-pp": {
               "type": "str",
               "item_type": "str",
               "label": "参数6",
               "require": 1,
               "choice": [],
               "range": "",
               "default": "/mnt/admin/model.pkl",
               "placeholder": "",
               "describe": "模型保存目录",
               "editable": 1,
               "condition": "",
               "sub_args": {}
           }
       }
   }
   ```

   * 添加 ner 训练任务流

     ![image-20220819135607546](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819135607546.png)

   * 进入 任务流，拖取 ner 训练任务模版 和 deploy-service 模版，并填写 任务启动参数

     

     ![image-20220819142546299](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819142546299.png)

     ![image-20220819135903909](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819135903909.png)‘

     * ner 训练任务参数解析

       `--model`: 训练的基础模型名称，这里固定为：`BiLSTM_CRF`。

       `--objectname`: 数据集的名字。

       `--epochs`: 训练的次数。

       `--path`：训练数据存放地址，即第三步获取数据存放的路径。

       `-pp`：模型保存目录，一般填写 `/mnt/admin/model.pkl` ，方便起服务的时候能够读取到模型路径。

     * deploy-service 任务参数解析

       

5. 保存模版，开始训练，点击日志，查看训练进度

   ![image-20220819140429808](/Users/zhuyaguang/Library/Application Support/typora-user-images/image-20220819140429808.png)

   

6. 部署服务

   同上，添加 ner-service 任务流

   

7. 使用服务






## 参考资料：

1. [博客](https://blog.csdn.net/zp563987805/article/details/104562798/?utm_medium=distribute.pc_relevant.none-task-blog-2~default~baidujs_baidulandingword~default-0--blog-119957026.pc_relevant_paycolumn_v3&spm=1001.2101.3001.4242.1&utm_relevant_index=3)
2. [github](https://github.com/BeHappyForMe/chinese-sequence-ner)



