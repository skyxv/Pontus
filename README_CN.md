Pontus
========
[![Support Python Version](https://img.shields.io/badge/Python-3.5|3.6-brightgreen.svg)](https://www.python.org/)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

[English](https://github.com/yandenghong/Pontus/blob/master/README.md)

Pontus 是一个简单的分布式的持续集成系统。

## 特性
* 组件之间采用TCP通信，支持扩展与分布式, 并保证了服务器之间连续，有序的数据流。
* 测试运行器自注册，轻松扩展。
* 同时处理多个请求的调度器。
* 全部依赖python内置库，开箱即用。

## 项目限制
* 该项目使用Git作为需要测试的代码的存储库。

* 仅运行存储库中名为tests的目录中的测试。

* 持续集成系统监视的主存储库通常托管在Web服务器上，在此项目中，使用本地存储库而不是远程存储库。

* Pontus系统每5秒运行一次检查, 它不会测试在这5秒内所做的每一次提交，只测试最近的提交。

* 此项目收集测试结果并将其作为文件存储在调度程序进程本地的文件系统中。

## Introduction
本系统的基本结构由三个部分组成：**observer**, **dispatcher**, **test runner**。

* observer: 监视存储库并在看到新提交时通知**dispatcher**。
* dispatcher: 用于委派测试任务的独立服务。监听来自**test runner**和**observer**的请求。
* test runner: 负责针对给定的提交ID运行测试并报告结果。

## 使用
构建Pontus系统将要监控的主存储库。
```text
mkdir test_repo
cd test_repo
git init
```

**observer**通过检查commit来工作，所以要在主存储库中至少有一次提交。
将tests文件夹从此代码库复制到test_repo并提交。
```text
cp -r /this/directory/tests /path/to/test_repo/ 
cd /path/to/test\_repo 
git add tests/ 
git commit -m ”add tests”
```

为**observer**创建一个主存储库的克隆库。
```text
git clone /path/to/test_repo test_repo_clone_obs
```

为**test runner**创建一个主存储库的克隆库。
```text
git clone /path/to/test_repo test_repo_clone_runner
```

运行(也可以使用 `nohup` 命令后台运行):
```text
python3 dispatcher.py

python3 test_runner.py <path/to/test_repo_clone_runner>

python3 repo_observer.py --dispatcher-server=localhost:8888 <path/to/repo_clone_obs>

```
在主存储库做一次新的提交：
```text
cd /path/to/test_repo
touch new_file
git add new_file
git commit -m"new file" new_file

```

测试结果存储在此代码库的`test_results/`文件夹中，使用提交ID作为文件名。
