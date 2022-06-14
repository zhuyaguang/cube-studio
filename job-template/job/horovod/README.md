# deploy-service 模板
镜像：ccr.ccs.tencentyun.com/cube-studio/horovod:20210401
k8s账号: kubeflow-pipeline
启动参数：
```bash
{
    "参数": {
        "--num_worker": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": 2,
            "placeholder": "",
            "describe": "",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        },
        "--python_file_path": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "/horovod/examples/tensorflow2/tensorflow2_mnist.py",
            "placeholder": "",
            "describe": "",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        },
        "--work_images": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "ccr.ccs.tencentyun.com/cube-studio/horovod:20210401",
            "placeholder": "",
            "describe": "",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        }
    }
}
```

