import time,datetime,logging,os,sys

dir_common = os.path.split(os.path.realpath(__file__))[0] + '/../'
sys.path.append(dir_common)   # 将根目录添加到系统目录,才能正常引用common文件夹

import argparse
import requests
import os,sys,datetime,time,json
from job.pkgs.k8s.py_k8s import K8s
from pathlib import Path

from threading import Thread
import pysnooper
import re
from kubernetes import client,config,watch
import uuid

base_dir = os.path.split(os.path.realpath(__file__))[0]
KFJ_NAMESPACE = os.getenv('KFJ_NAMESPACE', '')
KFJ_TASK_ID = os.getenv('KFJ_TASK_ID', '')
# KFJ_TASK_NAME = os.getenv('KFJ_TASK_NAME', '')
KFJ_TASK_NAME = "mpijob-" + str(uuid.uuid1())
task_node_selectors = re.split(',|;|\n|\t', os.getenv('KFJ_TASK_NODE_SELECTOR', ''))
KFJ_TASK_NODE_SELECTOR = {}
for task_node_selector in task_node_selectors:
    KFJ_TASK_NODE_SELECTOR[task_node_selector.split('=')[0]] = task_node_selector.split('=')[1]


KFJ_PIPELINE_ID = os.getenv('KFJ_PIPELINE_ID', '')
KFJ_RUN_ID = os.getenv('KFJ_RUN_ID', '')
KFJ_CREATOR = os.getenv('KFJ_CREATOR', '')
KFJ_RUNNER = os.getenv('KFJ_RUNNER')
KFJ_PIPELINE_NAME = os.getenv('KFJ_PIPELINE_NAME', '')
KFJ_TASK_IMAGES = os.getenv('KFJ_TASK_IMAGES', '')
KFJ_TASK_VOLUME_MOUNT = os.getenv('KFJ_TASK_VOLUME_MOUNT', '')
KFJ_TASK_RESOURCE_CPU = os.getenv('KFJ_TASK_RESOURCE_CPU', '')
KFJ_TASK_RESOURCE_MEMORY = os.getenv('KFJ_TASK_RESOURCE_MEMORY', '')
NUM_WORKER = 3
PYTHON_FILE_PATH=''


def get_volume_mounts(volume_mount,username):
    k8s_volumes = []
    k8s_volume_mounts = []
    if volume_mount and ":" in volume_mount:
        volume_mount = volume_mount.strip()
        if volume_mount:
            volume_mounts_temp = re.split(',|;', volume_mount)
            volume_mounts_temp = [volume_mount_temp.strip() for volume_mount_temp in volume_mounts_temp if volume_mount_temp.strip()]

            for volume_mount in volume_mounts_temp:
                volume, mount = volume_mount.split(":")[0].strip(), volume_mount.split(":")[1].strip()
                if "(pvc)" in volume:
                    pvc_name = volume.replace('(pvc)', '').replace(' ', '')
                    volumn_name = pvc_name.replace('_', '-').lower()
                    k8s_volumes.append({
                        "name":volumn_name,
                        "persistentVolumeClaim":{
                            "claimName":pvc_name
                        }
                    })
                    k8s_volume_mounts.append(
                        {
                            "name":volumn_name,
                            "mountPath":os.path.join(mount, username),
                            "subPath":username
                        }
                    )

                if "(hostpath)" in volume:
                    hostpath_name = volume.replace('(hostpath)', '').replace(' ', '')
                    temps = re.split('_|\.|/', hostpath_name)
                    temps = [temp for temp in temps if temp]
                    volumn_name = '-'.join(temps).lower()  # hostpath_name.replace('_', '-').replace('/', '-').replace('.', '-')
                    k8s_volumes.append(
                        {
                            "name":volumn_name,
                            "hostPath":{
                                "path":hostpath_name
                            }
                        }
                    )
                    k8s_volume_mounts.append({
                        "name":volumn_name,
                        "mountPath":mount
                    })

                if "(configmap)" in volume:
                    configmap_name = volume.replace('(configmap)', '').replace(' ', '')
                    volumn_name = configmap_name.replace('_', '-').replace('/', '-').replace('.', '-').lower()
                    k8s_volumes.append({
                        "name":volumn_name,
                        "configMap":{
                            "name":configmap_name
                        }
                    })

                    k8s_volume_mounts.append({
                        "name":volumn_name,
                        "mountPath":mount
                    })

    return k8s_volumes,k8s_volume_mounts


k8s_volumes, k8s_volume_mounts = get_volume_mounts(KFJ_TASK_VOLUME_MOUNT,KFJ_CREATOR)


# k8s_volumes.append(
#     {
#         "name": "dshm",
#         "emptyDir": {
#             "medium": "Memory"
#         }
#     }
# )

k8s_volume_mounts.append(
    {
        "name":'tz-config',
        "mountPath":"/etc/localtime"
    }
)



k8s_volumes.append(
    {
        "name": "tz-config",
        "hostPath": {
            "path": '/usr/share/zoneinfo/Asia/Shanghai'
        }
    }
)

# k8s_volume_mounts.append(
#     {
#         "name":'dshm',
#         "mountPath":"/dev/shm"
#     }
# )

print(k8s_volumes)
print(k8s_volume_mounts)

GPU_TYPE= os.getenv('KFJ_GPU_TYPE', 'NVIDIA')
GPU_RESOURCE= os.getenv('KFJ_TASK_RESOURCE_GPU', '0')
print(GPU_TYPE,GPU_RESOURCE)

CRD_INFO={
    "group": "kubeflow.org",
    "version": "v1",
    "plural": "mpijobs",
    'kind': 'MPIJob',
    "timeout": 60 * 60 * 24 * 2
}



# @pysnooper.snoop()
def make_mpijob(name):
    mpijob={
        "apiVersion": "kubeflow.org/v1",
        "kind": "MPIJob",
        "metadata": {
            "name": name,
            "namespace":KFJ_NAMESPACE,
            "labels": {
                "run-id": os.getenv('KFJ_RUN_ID', 'unknown'),
                "run-rtx": os.getenv('KFJ_RUNNER', 'unknown'),
                "pipeline-rtx": os.getenv('KFJ_CREATOR', 'unknown'),
                "task-id": os.getenv('KFJ_TASK_ID', 'unknown'),
                "pipeline-id": os.getenv('KFJ_PIPELINE_ID', 'unknown')
            }
        },
        "spec": {
            "slotsPerWorker": 1,
            "cleanPodPolicy": "Running",
            "mpiReplicaSpecs": {
                "Launcher": {
                    "replicas": 1,
                    "template": {
                        "metadata": {
                            "labels": {
                                "pipeline-id": KFJ_PIPELINE_ID,
                                "pipeline-name": KFJ_PIPELINE_NAME,
                                "task-name": KFJ_TASK_NAME,
                                'rtx-user': KFJ_RUNNER,
                                "component": name,
                                "type": "mpijob",
                                "run-id": os.getenv('KFJ_RUN_ID', 'unknown'),
                            }
                        },
                        "spec": {
                            "volumes": k8s_volumes,
                            "imagePullSecrets": [
                                {
                                    "name": "hubsecret"
                                },
                                {
                                    "name": "csig-hubsecret"
                                }
                            ],

                            "containers": [
                                {
                                    "image": "csighub.tencentyun.com/tme-kubeflow/horovod:cpu-20210401",
                                    "name": "mpi-launcher",
                                    "command": [
                                        "mpirun"
                                    ],
                                    "args": [
                                        "-np",
                                        str(NUM_WORKER),
                                        "--allow-run-as-root",
                                        "-bind-to",
                                        "none",
                                        "-map-by",
                                        "slot",
                                        "-x",
                                        "LD_LIBRARY_PATH",
                                        "-x",
                                        "PATH",
                                        "-mca",
                                        "pml",
                                        "ob1",
                                        "-mca",
                                        "btl",
                                        "^openib",
                                        "python",
                                        PYTHON_FILE_PATH
                                    ],
                                    "env": [
                                        {
                                            "name": "MY_CPU_REQUEST",
                                            "valueFrom": {
                                                "resourceFieldRef": {
                                                    "resource": "requests.cpu"
                                                }
                                            }
                                        }
                                    ],
                                    "resources": {
                                        "requests": {
                                            "cpu": KFJ_TASK_RESOURCE_CPU,
                                            "memory": KFJ_TASK_RESOURCE_MEMORY,
                                        },
                                        "limits": {
                                            "cpu": KFJ_TASK_RESOURCE_CPU,
                                            "memory": KFJ_TASK_RESOURCE_MEMORY
                                        }
                                    },
                                    "volumeMounts": k8s_volume_mounts,
                                }
                            ]
                        }
                    }
                },
                "Worker": {
                    "replicas": NUM_WORKER,
                    "template": {
                        "metadata": {
                            "labels": {
                                "pipeline-id": KFJ_PIPELINE_ID,
                                "pipeline-name": KFJ_PIPELINE_NAME,
                                "task-name": KFJ_TASK_NAME,
                                'rtx-user': KFJ_RUNNER,
                                "component": name,
                                "type": "mpijob",
                                "run-id": os.getenv('KFJ_RUN_ID', 'unknown'),
                            }
                        },
                        "spec": {
                            "volumes": k8s_volumes,
                            "imagePullSecrets": [
                                {
                                    "name": "hubsecret"
                                },
                                {
                                    "name": "csig-hubsecret"
                                }
                            ],
                            "affinity": {
                                "nodeAffinity": {
                                    "requiredDuringSchedulingIgnoredDuringExecution": {
                                        "nodeSelectorTerms": [
                                            {
                                                "matchExpressions": [
                                                    {
                                                        "key": node_selector_key,
                                                        "operator": "In",
                                                        "values": [
                                                            KFJ_TASK_NODE_SELECTOR[node_selector_key]
                                                        ]
                                                    } for node_selector_key in KFJ_TASK_NODE_SELECTOR
                                                ]
                                            }
                                        ]
                                    }
                                },
                                "podAntiAffinity": {
                                    "preferredDuringSchedulingIgnoredDuringExecution": [
                                        {
                                            "weight": 5,
                                            "podAffinityTerm": {
                                                "topologyKey": "kubernetes.io/hostname",
                                                "labelSelector": {
                                                    "matchLabels": {
                                                        "component": name,
                                                        "type":"mpijob"
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            },
                            "containers": [
                                {
                                    "image": "csighub.tencentyun.com/tme-kubeflow/horovod:cpu-20210401",
                                    "name": "mpi-worker",
                                    "env": [
                                        {
                                            "name": "MY_CPU_REQUEST",
                                            "valueFrom": {
                                                "resourceFieldRef": {
                                                    "resource": "requests.cpu"
                                                }
                                            }
                                        }
                                    ],
                                    "resources": {
                                        "requests": {
                                            "cpu": KFJ_TASK_RESOURCE_CPU,
                                            "memory": KFJ_TASK_RESOURCE_MEMORY,
                                        },
                                        "limits": {
                                            "cpu": KFJ_TASK_RESOURCE_CPU,
                                            "memory": KFJ_TASK_RESOURCE_MEMORY
                                        }
                                    },
                                    "volumeMounts": k8s_volume_mounts,
                                }
                            ]
                        }
                    }
                }
            }
        }
    }



    if GPU_TYPE=='NVIDIA' and GPU_RESOURCE:
        mpijob['spec']['mpiReplicaSpecs']['Worker']['template']['spec']['containers'][0]['resources']['requests']['nvidia.com/gpu'] = GPU_RESOURCE.split(',')[0]
        mpijob['spec']['mpiReplicaSpecs']['Worker']['template']['spec']['containers'][0]['resources']['limits']['nvidia.com/gpu'] = GPU_RESOURCE.split(',')[0]

    if GPU_TYPE=='TENCENT' and GPU_RESOURCE:
        if len(GPU_RESOURCE.split(','))==2:
            gpu_core,gpu_mem = GPU_RESOURCE.split(',')[0],str(4*int(GPU_RESOURCE.split(',')[1]))
            if gpu_core and gpu_mem:
                mpijob['spec']['mpiReplicaSpecs']['Worker']['template']['spec']['containers'][0]['resources']['requests'][
                    'tencent.com/vcuda-core'] = gpu_core
                mpijob['spec']['mpiReplicaSpecs']['Worker']['template']['spec']['containers'][0]['resources']['requests'][
                    'tencent.com/vcuda-memory'] = gpu_mem
                mpijob['spec']['mpiReplicaSpecs']['Worker']['template']['spec']['containers'][0]['resources']['limits'][
                    'tencent.com/vcuda-core'] = gpu_core
                mpijob['spec']['mpiReplicaSpecs']['Worker']['template']['spec']['containers'][0]['resources']['limits'][
                    'tencent.com/vcuda-memory'] = gpu_mem

    return mpijob



# 实时跟踪指定pod日志，直到pod结束
def watch_pod_log(name,namespace,container='main'):
    print('begin follow log')
    w = watch.Watch()
    for event in w.stream(client.CoreV1Api().read_namespaced_pod_log, name=name, namespace=namespace,container=container):
        print(event)

    print('end follow log')


@pysnooper.snoop()
def main():
    k8s_client = K8s()

    # 删除旧的mpi
    if KFJ_RUN_ID:
        print('begin delete old mpijob: run-id %s'%KFJ_RUN_ID)
        k8s_client.delete_crd(group=CRD_INFO['group'],
                              version=CRD_INFO['version'],
                              plural=CRD_INFO['plural'],
                              namespace=KFJ_NAMESPACE,
                              labels={"run-id":KFJ_RUN_ID})
        time.sleep(20)

    mpijob_json = make_mpijob(KFJ_TASK_NAME)
    print('begin create new mpijob: run-id %s' % KFJ_TASK_NAME)
    k8s_client.create_crd(
        group=CRD_INFO['group'],
        version=CRD_INFO['version'],
        plural=CRD_INFO['plural'],
        namespace=KFJ_NAMESPACE,
        body=mpijob_json
    )
    # 等待创建完成
    time.sleep(20)

    pods = k8s_client.get_pods(namespace=KFJ_NAMESPACE,labels={
        "job-name": "%s-launcher"%KFJ_TASK_NAME,
        "mpi_job_name": KFJ_TASK_NAME
    })
    if pods:
        pod=pods[0]
        print('begin listen mpijob launcher pod %s' % pod['name'])
        k8s_client.watch_pod_log(name=pod['name'],namespace=KFJ_NAMESPACE)
        crd = k8s_client.get_one_crd(
            group=CRD_INFO['group'],
            version=CRD_INFO['version'],
            plural=CRD_INFO['plural'],
            namespace=KFJ_NAMESPACE,
            name=KFJ_TASK_NAME
        )
        print('begin delete mpijob %s' % KFJ_TASK_NAME)
        # 删除旧的mpi
        if KFJ_RUN_ID:
            k8s_client.delete_crd(group=CRD_INFO['group'],
                                  version=CRD_INFO['version'],
                                  plural=CRD_INFO['plural'],
                                  namespace=KFJ_NAMESPACE,
                                  labels={"run-id": KFJ_RUN_ID})
        print(crd)
        if crd['status']=='Succeeded':
            exit(0)
        else:
            exit(1)
    else:
        print('cluster fail build')
        print('begin delete mpijob %s' % KFJ_TASK_NAME)
        # 删除旧的mpi
        if KFJ_RUN_ID:
            k8s_client.delete_crd(group=CRD_INFO['group'],
                                  version=CRD_INFO['version'],
                                  plural=CRD_INFO['plural'],
                                  namespace=KFJ_NAMESPACE,
                                  labels={"run-id": KFJ_RUN_ID})

        exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='nni config')
    parser.add_argument('--num_worker', type=int, default=2, help='并行worker的数目 (default: 2)')
    parser.add_argument('--python_file_path', type=str, default='', help='启动文件地址')

    args = parser.parse_args()
    print(args)
    NUM_WORKER = args.num_worker
    PYTHON_FILE_PATH = args.python_file_path
    main()





# python start.py --trial_code_directory /mnt/pengluan/nni/demo  --trial_command 'python mnist.py'







