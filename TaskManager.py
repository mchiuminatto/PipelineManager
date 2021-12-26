import zmq
import time
import numpy.random
import sys
import random
import argparse
import importlib
import copy
import os
import json

from SBConfig import SBConfig

# import logging


class EndPoint:
    """
    Implements a network endpoint abstraction

    """

    def __init__(self, protocol="tcp", ip="127.0.0.1", port="5557"):
        self._protocol = protocol
        self._ip = ip
        self._port = port

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, protocol):
        self._protocol = protocol

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):
        self._ip = ip

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port


class Task:

    TASK_DELAY = 1  # seconds

    def __init__(self, task_config):

        self.message_count = 0
        self._config = task_config
        self._task_id = f"{self._config['task_id']}_{random.randrange(1, 10005)}"
        self._task_type = self._config["task_type"]

        # endpoint assignment
        #self.record_log("************** > " + self._config)

        # print(self._mode)

        _connected = False
        self._context = zmq.Context()

        # connect queues
        _conn_descr = ""
        if self._config["task_type"] == "STARTER":
            # in OUT_ONLY mode, there is only one sink (output) queue where to push data
            # this is generally the first task of a process or the InitTask
            self._sink_edp = EndPoint(**self._config["sink_endpoint"])
            self._sink_socket = self._context.socket(zmq.PUSH)
            self._sink_uri = f"{self._sink_edp.protocol}://{self._sink_edp.ip}:{self._sink_edp.port}"
            self._sink_socket.bind(self._sink_uri)
            _conn_descr= f"{self._config['task_type']}, outbound uri {self._sink_uri}"
            _connected = True

        if self._config["task_type"] == "END":
            # in IN_ONLY mode, there is only one source queue (input) from where to pull data.
            # this is generally the case for the last task of a process
            self._source_edp = EndPoint(**self._config["source_endpoint"])
            self._source_socket = self._context.socket(zmq.PULL)
            self._source_uri = f"{self._source_edp.protocol}://{self._source_edp.ip}:{self._source_edp.port}"
            self._source_socket.connect(self._source_uri)
            _conn_descr = f"{self._config['task_type']}, inbound uri {self._source_uri}"
            _connected = True

        if self._config["task_type"] == "MIDDLE":
            # in IN_OUT mode there are three  source queue (input) from where to pull data, and a sink (output) queue where to
            # push data.
            # source (inbound) queue
            self._source_edp = EndPoint(**self._config["source_endpoint"])
            self._sink_edp = EndPoint(**self._config["sink_endpoint"])
            # middle endpoint is were the produced data will be taken by the sink process
            self._middle_edp = copy.deepcopy(self._sink_edp)
            self._middle_edp.port = str(int(self._middle_edp.port) + 1000)

            self._source_socket = self._context.socket(zmq.PULL)
            self._source_uri = f"{self._source_edp.protocol}://{self._source_edp.ip}:{self._source_edp.port}"
            self._source_socket.connect(self._source_uri)
            # middle (outbound) queue
            self._middle_socket = self._context.socket(zmq.PUSH)
            self._middle_uri = f"{self._middle_edp.protocol}://{self._middle_edp.ip}:{self._middle_edp.port}"
            self._middle_socket.connect(self._middle_uri)
            _conn_descr = f"{self._config['task_type']}, inbound uri, {self._source_uri}, outbound uri {self._middle_uri}"
            _connected = True

        if self._config["task_type"] == "MIDDLE_SINK":
            # in MIDDLE_SINK mode there are three
            # push data.
            # source (inbound) queue

            self._sink_edp = EndPoint(**self._config["sink_endpoint"])
            # middle endpoint is the source queue in this case
            self._middle_edp = copy.deepcopy(self._sink_edp)
            self._middle_edp.port = str(int(self._middle_edp.port) + 1000)

            # middle (inbound) queue
            self._middle_socket = self._context.socket(zmq.PULL)
            self._middle_uri = f"{self._middle_edp.protocol}://{self._middle_edp.ip}:{self._middle_edp.port}"
            self._middle_socket.bind(self._middle_uri)

            # sink (outbound) queue
            self._sink_socket = self._context.socket(zmq.PUSH)
            self._sink_uri = f"{self._sink_edp.protocol}://{self._sink_edp.ip}:{self._sink_edp.port}"
            self._sink_socket.bind(self._sink_uri)
            _conn_descr = f"{self._config['task_type']}, inbound uri, {self._middle_uri}, outbound uri {self._sink_uri}"
            _connected = True

        if not _connected:
            self.record_log("Task neither connected to source nor sink", type="ERROR")
            raise Exception("Task neither connected to source nor sink")


        self.cycle_counter = 0
        self.record_log(f"Task started / conn :{_conn_descr}")

    def __del__(self):

        try:
            self._source_socket.close()
        except Exception:
            self.record_log("No source socket to close", type="ERROR")

        try:
            self._sink_socket.close()
        except Exception:
            self.record_log("No sink socket to close", type="ERROR")

        try:
            self._middle_socket.close()
        except Exception:
            self.record_log("No middle socket to close", type="ERROR")

    def write_count(self):
        self.message_count += 1
        _pid = os.getpid()
        _message = {"proc_count":self.message_count}
        with open(f"./output/{_pid}.json", "w") as fp:
            json.dump(_message,fp)

    def middle_sink_worker(self, payload, **params):
        # self.message_count += 1
        self.record_log(f"Message count {self.message_count}")
        return payload

    def prepare_business(self):

        if self._task_type in ["STARTER", "MIDDLE", "END"]:
            _module = importlib.import_module(self._config["business"]["module"])
            _class = getattr(_module, self._config["business"]["class"])
            _object = _class(**self._config["business"]["instance_parameters"])
            self.worker_method = getattr(_object, self._config["business"]["worker"])
        elif self._task_type == "MIDDLE_SINK":
            self.worker_method = self.middle_sink_worker
        else:
            raise Exception("Invalid task type " + self._task_type)

    def continue_processing(self):
        if self._config["lifecycle"] == "infinite":
            return True
        else:
            if self.cycle_counter == 0:
                self.cycle_counter += 1
                return True

        return False

    def initiating_task_loop(self, **params):
        while True:
            if self.continue_processing():
                _product = self.worker_method(**params)
                if _product is not None:
                    #self.write_count()
                    self.record_log("There is a product to process, sending to outbound queue")

                    if (type(_product) == dict) or (type(_product) == str):
                        self.record_log(f"Product is a dictionary {_product}")
                        self._sink_socket.send_json(_product)
                        self.record_log(f"Product sent  {_product}" )
                    elif type(_product) == list:
                        self.record_log("Product is a list of items ")
                        for _p in _product:
                            self.record_log(f"Sending {_p}")
                            self._sink_socket.send_json(_p)
                            time.sleep(self.TASK_DELAY)
                    else:
                        self.record_log(str(_product) + "is not recognizable ", type="ERROR")

            time.sleep(self.TASK_DELAY)

    def middle_task_loop(self, **params):

        while True:
            self.record_log("Listening")
            if self.continue_processing():
                # receive

                _inbound_payload = self._source_socket.recv_json()
                if _inbound_payload is not None:
                    # self.write_count()
                    self.record_log("Received payload " + str(_inbound_payload))
                    # transform
                    _product = self.worker_method(_inbound_payload, **params)
                    self.record_log("Produced " + str(_product))

                    # forwards
                    _outbound_payload = list()
                    if type(_product) != list:
                        _outbound_payload.append(_product)
                    else:
                        _outbound_payload = _product

                    self.record_log(f"Sending payload {_outbound_payload}")
                    for _p in _outbound_payload:
                        self.record_log(f"Sending {_p}")
                        self._middle_socket.send_json(_p)
                        time.sleep(self.TASK_DELAY)

            time.sleep(self.TASK_DELAY)

    def middle_sink_task_loop(self, **params):

        while True:
            self.record_log("Listening")
            if self.continue_processing():
                # receive

                _inbound_payload = self._middle_socket.recv_json()
                if _inbound_payload is not None:
                    self.write_count()
                    self.record_log("Received payload " + str(_inbound_payload))
                    # transform
                    _product = self.worker_method(_inbound_payload, **params)
                    self.record_log("Produced " + str(_product))

                    # forwards
                    _outbound_payload = list()
                    if type(_product) != list:
                        _outbound_payload.append(_product)
                    else:
                        _outbound_payload = _product

                    self.record_log(f"Sending payload {_outbound_payload}")
                    for _p in _outbound_payload:
                        self.record_log(f"Sending {_p}")
                        self._sink_socket.send_json(_p)
                        time.sleep(self.TASK_DELAY)

            time.sleep(self.TASK_DELAY)

    def ending_task_loop(self, **params):

        while True:
            if self.continue_processing():
                _inbound_payload = None
                # print("Processing ", self._mode)

                _inbound_payload = self._source_socket.recv_json()
                if _inbound_payload is not None:
                    # self.write_count()
                    self.record_log(f'received {_inbound_payload}')
                    print("DEBUG ", _inbound_payload)
                    _product = self.worker_method(_inbound_payload, **params)
                    self.record_log(f"Produced {_product}")

            time.sleep(self.TASK_DELAY)

    def working_loop(self, **params):
        if self._task_type == "STARTER":
            # starter working loop
            self.initiating_task_loop(**params)
        elif self._task_type == "END":
            # ending task work loop
            self.ending_task_loop(**params)
        elif self._task_type == "MIDDLE":
            # middle task working loop
            self.middle_task_loop(**params)
        elif self._task_type == "MIDDLE_SINK":
            # middle task's sink
            self.middle_sink_task_loop(**params)
        else:
            raise Exception("Invalid task type " + self._task_type)

    def record_log(self,  message, type="INFO"):
        if type == "INFO":
            #logging.info(message)
            print("INFO - " + message)
        else:
            #logging.error(message)
            print("ERROR - " + message)

        #print(f"{type} - {self._task_id} - {message}")



if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--config_folder', '-d', help="Configuration folder", type=str)
    parser.add_argument('--config_file', '-f', help="Configuration file (json format)", type=str)

    print(parser.format_help())
    args = parser.parse_args()

    print(args)

    if args.config_folder is None:
        print("ERROR: --config_folder is not optional")
        exit(-1)

    if args.config_file is None:
        print("ERROR: --config file is not optional")
        exit(-1)

    _tsk = Task(args.config_folder, args.config_file)
    _tsk.prepare_business()
    _tsk.working_loop()
