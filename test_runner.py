import argparse
import os
import re
import threading
import time
import socket
import socketserver
import unittest

import helpers


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    dispatcher_server = None  # Holds the dispatcher server host/port information
    last_communication = 0  # Keeps track of last communication from dispatcher
    busy = False  # Status flag
    dead = False  # Status flag


def dispatcher_checker(server):
        while not server.dead:
            time.sleep(5)
            if (time.time() - server.last_communication) > 10:
                try:
                    response = helpers.communicate(
                                       server.dispatcher_server["host"],
                                       int(server.dispatcher_server["port"]),
                                       "status")
                    if response != "OK":
                        print("Dispatcher is no longer functional")
                        server.shutdown()
                        return
                except socket.error as e:
                    print("Can't communicate with dispatcher: %s" % e)
                    server.shutdown()
                    return


class TestHandler(socketserver.BaseRequestHandler):
    command_re = re.compile(r"(\w+)(:.+)*")
    BUF_SIZE = 1024

    def handle(self):
        self.data = self.request.recv(self.BUF_SIZE).decode().strip()
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            self.request.sendall("Invalid command")
            return
        command = command_groups.group(1)
        if command == "ping":
            print("pinged")
            self.server.last_communication = time.time()
            self.request.sendall("pong".encode())
        elif command == "runtest":
            print("got runtest command: am I busy? %s" % self.server.busy)
            if self.server.busy:
                self.request.sendall("BUSY".encode())
            else:
                self.request.sendall("OK".encode())
                print("running")
                commit_id = command_groups.group(2)[1:]
                self.server.busy = True
                self.run_tests(commit_id,
                               self.server.repo_folder)
                self.server.busy = False

    @staticmethod
    def update_repo(repo_path, commit_id):
        os.chdir(repo_path)
        err = os.system("git clean -d -f -x")
        if err:
            print("Can not clean repository")
            return
        err = os.system("git pull")
        if err:
            print("Can not run `git pull` command")
            return
        err = os.system("git reset --hard {}".format(commit_id))
        if err:
            print("Can not update to given commit hash")
            return

    def run_tests(self, commit_id, repo_folder):
        # update repo
        self.update_repo(repo_folder, commit_id)
        # run the tests
        test_folder = os.path.join(repo_folder, "tests")
        suite = unittest.TestLoader().discover(test_folder)
        result_file = open("results", "w")
        unittest.TextTestRunner(result_file).run(suite)
        result_file.close()
        result_file = open("results", "r")
        # give the dispatcher the results
        output = result_file.read()
        helpers.communicate(self.server.dispatcher_server["host"],
                            int(self.server.dispatcher_server["port"]),
                            "results:%s:%s:%s" % (commit_id, len(output), output))


def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="test runner's host, by default it uses localhost",
                        default="localhost",
                        action="store")
    parser.add_argument("--port",
                        help="test runner's port, by default it uses 8999",
                        default=8999,
                        action="store")
    parser.add_argument("--dispatcher-server",
                        help="dispatcher host:port, " \
                             "by default it uses localhost:8888",
                        default="localhost:8888",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repository this will run test")
    args = parser.parse_args()
    server = ThreadingTCPServer((args.host, int(args.port)), TestHandler)
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")
    server.dispatcher_server = {"host": dispatcher_host, "port": dispatcher_port}
    server.repo_folder = args.repo
    print("serving on % s: % s" % (args.host, int(args.port)))
    helpers.communicate(dispatcher_host, int(dispatcher_port), "register:%s:%s" % (args.host, int(args.port)))
    print("registered to % s: % s" % (dispatcher_host, dispatcher_port))
    dispatcher_check = threading.Thread(target=dispatcher_checker, args=(server,))
    try:
        dispatcher_check.start()
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl+C or Cmd+C
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        # if any exception occurs, kill the thread
        server.dead = True
        dispatcher_check.join()


if __name__ == '__main__':
    serve()
