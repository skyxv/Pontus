import os
import re
import time
import socket
import argparse
import threading
import socketserver

import helpers


def dispatch_tests(server, commit_id):
    while True:
        print("trying to dispatch to runners")
        for runner in server.runners:
            response = helpers.communicate(runner["host"],
                                           int(runner["port"]),
                                           "runtest:%s" % commit_id)
            if response == "OK":
                print("adding id %s" % commit_id)
                server.dispatched_commits[commit_id] = runner
                if commit_id in server.pending_commits:
                    server.pending_commits.remove(commit_id)
                return
        time.sleep(2)


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    runners = []  # Keeps track of test runner pool
    dead = False  # Indicate to other threads that we are no longer running
    dispatched_commits = {}  # Keeps track of commits we dispatched
    pending_commits = []  # Keeps track of commits we have yet to dispatch


class DispatcherHandler(socketserver.BaseRequestHandler):
    """
    The RequestHandler class for dispatcher.
    This will dispatch test runners against the incoming commit
    and handle their requests and test results
    """
    command_re = re.compile(r"(\w+)(:.+)*")
    BUF_SIZE = 1024

    def handle(self):
        self.data = self.request.recv(self.BUF_SIZE).decode().strip()
        command_groups = self.command_re.match(self.data)
        if not command_groups:
            self.request.sendall("Invalid command".encode())
            return
        command = command_groups.group(1)
        if command == "status":
            print("in status")
            self.request.sendall("OK".encode())
        elif command == "register":
            # Add this test runner to our pool
            print("register")
            address = command_groups.group(2)
            host, port = re.findall(r":(\w*)", address)
            runner = {"host": host, "port": port}
            self.server.runners.append(runner)
            self.request.sendall("OK".encode())
        elif command == "dispatch":
            print("going to dispatch")
            commit_id = command_groups.group(2)[1:]
            if not self.server.runners:
                self.request.sendall("No runners are registered".encode())
            else:
                self.request.sendall("OK".encode())
                dispatch_tests(self.server, commit_id)
        elif command == "results":
            print("got test results")
            results = command_groups.group(2)[1:]
            results = results.split(":")
            commit_id = results[0]
            length_msg = int(results[1])
            # 3 is the number of ":" in the sent command
            remaining_buffer = self.BUF_SIZE - \
                               (len(command) + len(commit_id) + len(results[1]) + 3)
            if length_msg > remaining_buffer:
                self.data += self.request.recv(length_msg - remaining_buffer).strip()
            del self.server.dispatched_commits[commit_id]
            if not os.path.exists("test_results"):
                os.makedirs("test_results")
            with open("test_results/%s" % commit_id, "w") as f:
                data = self.data.split(":")[3:]
                data = "\n".join(data)
                f.write(data)
            self.request.sendall("OK".encode())


class Dispatcher:
    """
    The dispatcher is a separate service used to delegate testing tasks.
    """
    def __init__(self, server: ThreadingTCPServer):
        self.server = server

    def _manage_commit_lists(self, runner):
        for commit, assigned_runner in self.server.dispatched_commits.iteritems():
            if assigned_runner == runner:
                del self.server.dispatched_commits[commit]
                self.server.pending_commits.append(commit)
                break
        self.server.runners.remove(runner)

    def _runner_checker(self):
        while not self.server.dead:
            time.sleep(1)
            for runner in self.server.runners:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    response = helpers.communicate(runner["host"],
                                                   int(runner["port"]),
                                                   "ping")
                    if response != "pong":
                        print("removing runner %s" % runner)
                        self._manage_commit_lists(runner)
                except Exception:
                    self._manage_commit_lists(runner)

    def _redistribute(self):
        while not self.server.dead:
            for commit in self.server.pending_commits:
                print("running redistribute")
                print(self.server.pending_commits)
                dispatch_tests(self.server, commit)
                time.sleep(5)

    def serve(self):
        runner_heartbeat = threading.Thread(target=self._runner_checker)
        redistributor = threading.Thread(target=self._redistribute)
        try:
            runner_heartbeat.start()
            redistributor.start()
            # Activate the server; this will keep running until you
            # interrupt the program with Ctrl+C or Cmd+C
            self.server.serve_forever()
        except (KeyboardInterrupt, Exception):
            # if any exception occurs, kill the thread
            self.server.dead = True
            runner_heartbeat.join()
            redistributor.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--host",
                        help="dispatcher's host, by default it uses localhost",
                        default="localhost",
                        action="store")
    parser.add_argument("--port",
                        help="dispatcher's port, by default it uses 8888",
                        default=8888,
                        action="store")
    args = parser.parse_args()
    print("serving on % s: % s" % (args.host, int(args.port)))
    dispatch_server = ThreadingTCPServer((args.host, int(args.port)), DispatcherHandler)
    dispatcher = Dispatcher(dispatch_server)
    dispatcher.serve()
