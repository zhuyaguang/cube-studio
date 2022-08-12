# download_minio 模板
镜像：ccr.ccs.tencentyun.com/cube-studio/download-minio:20220812
启动参数：
```bash
{
    "参数分组1": {
        "--bucket_name": {
            "type": "str",
            "item_type": "str",
            "label": "参数1",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "test",
            "placeholder": "",
            "describe": "minio bucket 名称",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        },
        "--output": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "/mnt/admin/",
            "placeholder": "",
            "describe": "保存从minio下载数据地址的目录 /mnt/admin/pre-train/ 记得后面加/",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        },
        "--minio_endpoint": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "10.101.32.11:9000",
            "placeholder": "",
            "describe": "minio的地址",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        },
        "--access_key": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "admin",
            "placeholder": "",
            "describe": "minio的用户名",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        },
        "--secret_key": {
            "type": "str",
            "item_type": "str",
            "label": "",
            "require": 1,
            "choice": [],
            "range": "",
            "default": "root123456",
            "placeholder": "",
            "describe": "minio的密码",
            "editable": 1,
            "condition": "",
            "sub_args": {}
        }
    }
}
```

说明：将某个 bucket 的数据下载到 指定目录。