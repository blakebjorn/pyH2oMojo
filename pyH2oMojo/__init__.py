name = "pyH2oMojo"

import socket
import json
import os
import time
import subprocess
from threading import Thread
from queue import Queue, Empty

class H2oMojoPredictor(object):
    def __init__(self, model, _type="multivariate", x_cols=None, x_types=None, connection_timeout=10.0, prediction_timeout=3.0, verbose=False):
        if _type not in ("multivariate", "regression", "ordinal", "binomial",
                         "autoencoder", "clustering", "dimreduction"):
            raise NotImplementedError("Only 'multivariate', 'regression', 'ordinal', 'binomial', 'autoencoder', "
                                      "'clustering', and 'dimreduction' are supported predictor types")
        if not os.path.isfile(model):
            raise FileNotFoundError("Model file not found.")

        self.buffer = subprocess.PIPE

        dir_path = os.path.dirname(os.path.realpath(__file__))

        self.subprocess = subprocess.Popen(["java", "-jar", os.path.join(dir_path, "pyH2oMojo-1.0.jar"), model, _type],
                                           stderr=self.buffer, stdout=self.buffer)
        self.queue = Queue()
        self.port = 54322
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.predictionTimeout = prediction_timeout
        self.verbose = verbose

        def enqueue_output(out, queue):
            for line in iter(out.readline, b''):
                queue.put(line)
            out.close()

        t = Thread(target=enqueue_output, args=(self.subprocess.stdout, self.queue))
        t.daemon = True  # thread dies with the program
        t.start()

        self.columnTypes = x_types
        self.trainingColumns = x_cols

        st = time.time()
        while True:
            try:
                line = self.queue.get_nowait()  # or q.get(timeout=.1)
                js = json.loads(line)
                self.port = js["port"]
                break
            except (Empty, KeyError):
                pass
            time.sleep(0.001)
            if time.time() - st > connection_timeout:
                raise RuntimeError("Could not start prediction server - timed out.")

        if self.verbose:
            print("Subprocess PID {} running on port {}".format(self.subprocess.pid, self.port))

    def predict(self, input_data):
        if self.trainingColumns:
            output = {x: input_data[x] for x in self.trainingColumns}
        if self.columnTypes:
            for x in self.columnTypes:
                if self.columnTypes[x] == "real" and x in output:
                    output[x] = float(output[x])
                elif self.columnTypes[x] == "int" and x in output:
                    output[x] = int(output[x])
                elif self.columnTypes[x] == "str" and x in output:
                    output[x] = str(output[x])
        else:
            output = {x: input_data[x] for x in input_data}
            for i in output:
                output[i] = float(output[i]) if isinstance(i, int) else output[i]

        outputstring = json.dumps(output).encode("utf8")

        st = time.time()
        while True:
            if self.verbose:
                print(">>> " + outputstring.decode("utf8"))
            self.sock.sendto(outputstring, ("127.0.0.1", self.port))
            try:
                line = self.queue.get_nowait()
                js = json.loads(line)
                for col in ('classProbabilities', 'calibratedClassProbabilities', 'distances'):
                    if col in js:
                        js[col] = json.loads(js[col])
                        js[col] = [round(x, 4) for x in js[col]]
                return js
            except Empty:
                pass
            if time.time() - st > self.predictionTimeout:
                raise ValueError("Prediction Timed Out")

    def read_input(self, timeout=0.5):
        st = time.time()
        while True:
            for line in iter(self.subprocess.stdout.readline, ''):
                if self.verbose:
                    print("<<< " + line.decode("utf8"))
                return True
            if time.time() - st > timeout:
                return False

    @staticmethod
    def supported_predictors():
        return ["multivariate", "regression", "ordinal", "binomial", "autoencoder", "clustering", "dimreduction"]

