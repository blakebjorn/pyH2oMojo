import sys

name = "pyH2oMojo"

import socket
import json
import os
import time
import subprocess
from threading import Thread
from queue import Queue, Empty
from math import isnan

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()


class H2oMojoPredictor(object):
    def __init__(self, model, _type="multivariate", x_cols=None, x_types=None, connection_timeout=10.0,
                 prediction_timeout=3.0, verbose=False):
        if _type not in ("multivariate", "regression", "ordinal", "binomial",
                         "autoencoder", "clustering", "dimreduction"):
            raise NotImplementedError("Only 'multivariate', 'regression', 'ordinal', 'binomial', 'autoencoder', "
                                      "'clustering', and 'dimreduction' are supported predictor types")
        if not os.path.isfile(model):
            raise FileNotFoundError("Model file not found.")

        self.buffer = subprocess.PIPE
        self.errorBuffer = subprocess.PIPE

        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.subprocess = subprocess.Popen(["java", "-jar", os.path.join(dir_path, "pyH2oMojo-1.0.jar"), model, _type],
                                           stderr=self.errorBuffer, stdout=self.buffer)

        self.queue = Queue()
        self.port = 54322
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.predictionTimeout = prediction_timeout
        self.verbose = verbose

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
        else:
            output = {x: input_data[x] for x in input_data}

        for i in output:
            output[i] = float(output[i]) if isinstance(i, int) else output[i]
            if isinstance(output[i], float) and isnan(output[i]):
                output[i] = "null"

        if self.columnTypes:
            for x in self.columnTypes:
                if self.columnTypes[x] == "real" and x in output:
                    output[x] = float(output[x]) if not isnan(float(output[x])) else "null"
                elif self.columnTypes[x] == "int" and x in output:
                    output[x] = int(output[x])
                elif self.columnTypes[x] == "str" and x in output:
                    output[x] = str(output[x])

        outputstring = json.dumps(output).encode("utf8")

        if self.verbose:
            print(">>> " + outputstring.decode("utf8"))

        t = Thread(target=enqueue_output, args=(self.subprocess.stdout, self.queue))
        t.daemon = True  # thread dies with the program
        t.start()

        self.sock.sendto(outputstring, ("127.0.0.1", self.port))
        st = time.time()
        while True:
            try:
                line = self.queue.get_nowait()
                js = json.loads(line)
                for col in ('classProbabilities', 'calibratedClassProbabilities', 'distances'):
                    if col in js:
                        js[col] = json.loads(js[col])
                        js[col] = [round(x, 5) for x in js[col]]
                if self.verbose:
                    print("<<<", js)
                return js
            except Empty:
                pass
            if time.time() - st > self.predictionTimeout:
                t2 = Thread(target=enqueue_output, args=(self.subprocess.stderr, self.queue))
                t2.daemon = True  # thread dies with the program
                t2.start()
                st = time.time()
                lineFound = False
                while True:
                    try:
                        line = self.queue.get_nowait()
                        lineFound = True
                        print("<<<", line.decode("utf8").rstrip(), file=sys.stderr)
                    except Empty:
                        if lineFound:
                            break
                    if time.time() - st > 1.0:
                        break
                raise ValueError("Prediction Timed Out")

    @staticmethod
    def supported_predictors():
        return ["multivariate", "regression", "ordinal", "binomial", "autoencoder", "clustering", "dimreduction"]
