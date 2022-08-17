# deploy-service 模板
镜像：ccr.ccs.tencentyun.com/cube-studio/mnist:20220814
启动参数：
```bash
{
    "shell": {
        "--modelpath": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "/mnt/admin/pytorch/model",
            "placeholder": "",
            "describe": "模型保存路径",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        }

    }
}
```