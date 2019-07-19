import os
import time
import socket
import argparse
import subprocess

import helpers


class RepoObserver:
    @staticmethod
    def get_commit_id():
        return str(subprocess.check_output(["git", "rev-parse", "HEAD"]), encoding="utf8").strip("\n")

    def update_repo(self, repo_path):
        os.chdir(repo_path)
        commit_id = self.get_commit_id()
        err = os.system("git pull")
        if err:
            print("Can not run `git pull` command")
            return
        new_commit_id = self.get_commit_id()
        if commit_id != new_commit_id:
            with open('./.commit_id', 'w') as f:
                f.write(new_commit_id)

    def poll(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--dispatcher-server",
                            help="dispatcher host:port, " \
                            "by default it uses localhost:8888",
                            default="localhost:8888",
                            action="store")
        parser.add_argument("repo", metavar="REPO", type=str,
                            help="path to the repository this will observe")
        args = parser.parse_args()
        dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")

        while True:
            try:
                # call the bash script that will update the repo and check
                # for changes. If there's a change, it will drop a .commit_id file
                # with the latest commit in the current working directory
                self.update_repo(args.repo)
            except Exception as e:
                raise Exception(e)
            if os.path.isfile(".commit_id"):
                try:
                    response = helpers.communicate(dispatcher_host,
                                                   int(dispatcher_port),
                                                   "status")
                except socket.error as e:
                    raise Exception("Could not communicate with dispatcher server: %s" % e)
                if response == "OK":
                    commit = ""
                    with open(".commit_id", "r") as f:
                        commit = f.readline()
                    response = helpers.communicate(dispatcher_host,
                                                   int(dispatcher_port),
                                                   "dispatch:%s" % commit)
                    if response != "OK":
                        raise Exception("Could not dispatch the test: %s" %
                                        response)
                    print("dispatched!")
                else:
                    raise Exception("Could not dispatch the test: %s" %
                                    response)
            time.sleep(5)


repo_observer = RepoObserver()

if __name__ == '__main__':
    repo_observer.poll()
