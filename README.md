Pontus
========
[![Support Python Version](https://img.shields.io/badge/Python-3.5|3.6-brightgreen.svg)](https://www.python.org/)
![License](https://img.shields.io/badge/License-MIT-blue.svg)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

[中文](https://github.com/yandenghong/Pontus/blob/master/README_CN.md)

Pontus is a simple distributed continuous integration system.

## Features
* TCP communication between components supports expansion and distribution, and ensures continuous and orderly data flow between servers.
* The test runner is self-registering and easy to extend.
* A dispatcher that handles multiple requests simultaneously.
* All rely on Python built-in libraries, Can be directly executed using `python3`after cloning.


## Project Limitations
* This project uses Git as the repository for the code that needs to be tested.

* Only run tests that are in a directory named tests within the repository.

* Continuous integration systems monitor a master repository which is usually hosted on a web server, and not local to the CI's file systems. In this project, use a local repository instead of a remote repository.

* The Pontus system runs a check every 5 seconds. It does not test every commit made in these 5 seconds, only the most recent commit.

* For simplicity, this project gathers the test results and stores them as files in the file system local to the dispatcher process.

## Introduction
The basic structure of a continuous integration system consists of three components: an **observer**, a **dispatcher**, and a **test runner**.

* observer: monitor a repository and notifies the **dispatcher** when a new commit is seen.
* dispatcher: a separate service used to delegate testing tasks.It listens on a port for requests from test runners and from the repository observer.
* test runner: the test runner is responsible for running tests against a given commit ID and reporting the results.


## Usage
set up the repository Pontus system will monitor.
```text
mkdir test_repo
cd test_repo
git init
```

The repository observer works by checking commits, so we need at least one commit in the master repository.
Copy the tests folder from this code base to test_repo and commit it.
```text
cp -r /this/directory/tests /path/to/test_repo/ 
cd /path/to/test\_repo 
git add tests/ 
git commit -m ”add tests”
```

create a clone of master repository for the repo observer component:
```text
git clone /path/to/test_repo test_repo_clone_obs
```

create a clone of master repository for the test runner component:
```text
git clone /path/to/test_repo test_repo_clone_runner
```

Running(also can using the `nohup` command):
```text
python3 dispatcher.py

python3 test_runner.py <path/to/test_repo_clone_runner>

python3 repo_observer.py --dispatcher-server=localhost:8888 <path/to/repo_clone_obs>

```
Now that everything is set up, let's trigger some tests! Go to your master repository:
```text
cd /path/to/test_repo
touch new_file
git add new_file
git commit -m"new file" new_file

```
the test results was stored in a `test_results/` folder in this code base, using the commit ID as the filename.
