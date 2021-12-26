import json as js
import importlib
import multiprocessing
from multiprocessing import Process
import time
from datetime import datetime as Dt
# import logging
import sys

from TaskManager import Task
from SBConfig import SBConfig



class Manager():
    TASK_TYPE_MAP = {"01": "STARTER",
                "11": "MIDDLE",
                "10": "END"}

    def __init__(self, config_folder: str, task_list_file: str):
        self._proc_table = None
        self._running_table = list()
        self.file_pt = None
        self._config_folder = config_folder
        self._task_list_file = task_list_file





    def __delete__(self, instance):
        self.kill_indicators()
        # self.save_proc_table()


    # *********************************************
    # PROPERTIES
    # *********************************************
    @property
    def proc_table(self):
        return self._proc_table
    @property
    def count_tasks(self):
        return len(self._proc_table["task_list"])

    # **************************************
    # STATE MACHINE HANDLER
    # **************************************

    def handler(self):
        """
            Implements the state machine
        """

        # 1. startup
        try:  # to startup the indicator table
            print('>>>>> STARTUP <<<<<<')
            self.startup()
        except Exception as e:
            print(f"Was not possible to load indicator's table {str(e)}")
            # logging.ERROR(f"Was not posible to load indicator's table {str(e)}")
            return

        # 2. spawn indicators processes
        try:  # to spawn indicators
            print('>>>>> SPAWN <<<<<<')
            self.spawn_tasks()
        except Exception as e:
            print(f"Error trying to spawn indicators: {str(e)}")
            # logging.error(f"Error trying to spawn indicators: {str(e)}")
            return

        while True:
            print('>>>>> MANAGE <<<<<<')
            self.manage_indicators()
            time.sleep(60)

        # 3 manage indicators

    #######################################################
    # MAIN METHODS
    ########################################################

    @staticmethod
    def run_task(task_config):

        _task = Task(task_config)  # instantiates a task
        _task.prepare_business()  # task's business logic preparation
        _task.working_loop()  # task working infinite loop

    def load_task_config(self, task_config_file):
        _task_config = SBConfig.read_config_file(self._config_folder, task_config_file)
        _mode = ["0", "0"]
        if _task_config["source_endpoint"] is not None:
            _mode[0] = "1"
        if _task_config["sink_endpoint"] is not None:
            _mode[1] = "1"

        _task_config["task_type"] = self.TASK_TYPE_MAP["".join(_mode)]

        return _task_config

    def spawn_tasks(self):

        #logging.info("Tasks count " + str(self.count_tasks))
        print("Tasks count " + str(self.count_tasks))
        for i in range(0, self.count_tasks):

            # load task list
            _task = self._proc_table["task_list"][i]
            # print(i, _task)

            # LOAD TASK CONFIGURATION
            _task_config = self.load_task_config(_task["task_config"])

            # loop spawning tasks instances
            for j in range(_task["instances"]):
                _p = Process(target=self.run_task, args=(_task_config, ))
                _p.start()

                _task_running_node = {"task":self._proc_table['task_list'][i]["task_id"],
                                      "description":self._proc_table['task_list'][i]["description"],
                                      "PID":_p.pid,
                                      "Alive":_p.is_alive(),
                                      "proc":_p}

                self._running_table.append(_task_running_node)
                # logging.info(f"Started {self._proc_table['task_list'][i]}")
                print(f"Started {self._proc_table['task_list'][i]}")

            if _task_config["task_type"] == "MIDDLE":
                # spawn a sink where middle task push their products

                _task_config["task_type"] = "MIDDLE_SINK"
                _p = Process(target=self.run_task, args=(_task_config,))
                _p.start()
                _task_running_node = {"task": self._proc_table['task_list'][i]["task_id"],
                                      "description": self._proc_table['task_list'][i]["description"] + "_sink",
                                      "PID": _p.pid,
                                      "Alive": _p.is_alive(),
                                      "proc": _p}

                self._running_table.append(_task_running_node)
                # logging.info(f"Started {_task_running_node['description']}")
                print(f"Started {_task_running_node['description']}")

        return

    def startup(self):
        # read the task list
        try:
            with open(self._config_folder+self._task_list_file,"r+") as fp:
                self._proc_table = js.load(fp)
        except Exception as e:
            raise Exception(e)

        #self.open_log("PPLN_MANAGER")
        #logging.info(" >>>>>>>>>>>>>>> MANAGER STARTED <<<<<<<<<<<<<<<<<<")

    def manage_indicators(self):

        for i in range(0, len(self._running_table)):
            _proc = self._running_table[i]["proc"]
            if _proc.is_alive():
                self._running_table[i]["Alive"] = "yes"
            else:
                self._running_table[i]["Alive"] = "no"
        self.print_status()

    def kill_indicators(self):
        for i in range(0, len(self._proc_table)):
            _proc = self._proc_table[i]["process"]
            _proc.terminate()
            if _proc.is_alive():
                self._proc_table[i]["is_alive"] = "yes"
            else:
                self._proc_table[i]["is_alive"] = "no"

    def save_proc_table(self):
        with open ("indicators.json","w") as ind_f:
            js.dump(self._proc_table, ind_f)

    # ###############################
    # SUPPORT METHODS
    # ##############################
    def print_status(self):

        _header = self.build_proc_header()
        print(_header)
        # logging.info(_header)
        _proc_list = self.build_proc_row()
        print(_proc_list)
        # logging.info(_proc_list)

    def build_col(self, width, text):
        _col = text + " "*(max(0, width - len(text)))
        return _col

    def build_proc_header(self):

        _col_width = 15
        _col_date = "\nReport Time " + Dt.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
        _col_task = "Task"
        _line = "\n" + self.build_col(_col_width, "Report Time " + Dt.now().strftime('%Y-%m-%d %H:%M:%S')) + "\n"
        _line += "\n" +  self.build_col(_col_width, "Task")+ "\t"
        _line += self.build_col(_col_width, "Description") + "\t"
        _line += self.build_col(_col_width, "PID") + "\t"
        _line += self.build_col(_col_width, "Running") + "\t"
        _line += self.build_col(_col_width, "Items Processed") + "\t"
        _line += "\n"
        _line += "_"*120 + "\n"
        return _line

    def build_proc_row(self):
        _col_width = 15
        _proc_list= ""
        for i in range(0, len(self._running_table)):

            _row = self._running_table[i]
            _file_name = f"{_row['PID']}.json"
            try:
                with open(f"./output/{_file_name}") as fp:
                    _pid_info = js.load(fp)
                _count = str(_pid_info["proc_count"])
            except FileNotFoundError:
                _count = " "

            _line = self.build_col(_col_width, _row["task"]) + "\t"
            _line += self.build_col(_col_width, _row["description"]) + "\t"
            _line += self.build_col(_col_width, str(_row["PID"])) + "\t"
            _line += self.build_col(_col_width, _row["Alive"]) + "\t"
            _line += self.build_col(_col_width, _count)
            _line += "\n"
            _proc_list += _line

        return _proc_list

    # def open_log(self, process_name):
    #     _date = Dt.today().strftime("%Y%m%d")
    #     _log_file_name = self._proc_table["log_folder"] + _date + "_" + f"{process_name}.log"
    #     logging.basicConfig(filename=_log_file_name, format="%(asctime)s %(levelname)s:%(message)s",
    #                         level=logging.INFO)



if __name__ == "__main__":
    _config_folder = sys.argv[1]
    _task_list = sys.argv[2]
    _man = Manager(_config_folder, _task_list)
    _man.handler()
