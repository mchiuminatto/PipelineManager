# Pipeline Setup

Pipeline Manager is a framework to run a sequence of tasks with the option to rune some on parallel taking advantages of a multi-core processor. It is based on zero mq so even though
 currently does not support clustered execution, with some few adjustments to read file from remote server could run in this mode.

This is a work in progress and contributions are welcome.


# Building a Module for the Pipeline

Building a module for the pipeline requires some few considerations.

Pass all possible parameters to constructor (hyperparameter)
Build a method to execute from the pipeline. The structure of this method (signature and return value) depends on the type of task being executed:

## Start task (STARTER)

The method requires no parameter in the signature and return the payload for the next task.


```python

def produce(**params):
    ...
    ...
	
	return payload

```

## Middle task (MIDDLE)
This method requires non-optional parameter to receive the payload form the previous task and return the payload for the next task.

```python

def produce(item, **params):
    ...
    ...
	
	return payload

```

## End (END)
For this task is required only a non-optional parameter to receive the payload form the previous task, and no return.

```python

def produce(item, **params):
    ...
    ...
	

```




# Setting up a task

For each task the pipeline needs to run, it is necessary to create a task setup file, like this one

```json
{
  "task_id": "task_1",
  "protocol": "tcp",
  "source_endpoint": null,
  "sink_endpoint": {"protocol": "tcp",
                    "ip": "127.0.0.1",
                    "port": 5557},
  "business": {
    "module": "Test.Lib.PipelineManager.Business",
    "class": "Business1",
    "worker": "perform_any_calculation",
    "instance_parameters": {}
  },
  "lifecycle": "infinite"
}
```

where:

- **task_id**: Is a task identification, which will be referenced from the task list that will be reviewed ahead in this manual.
- **protocol**: Zero MQ transport protocol
- **source_endpoint**: Is the address of the input queue if any (see endpoint)
- **sink_endpoint**: Is the address of the sink (output) queue (see endpoint)
- **business**: Business logic configuration section
- **lifecycle**: establish how long a task runs: ***infinite***: forever, ***once***: only one cycle.

**endpoint**: Is a queue address and has the following structure

```json
{"protocol": "tcp",
  "ip": "127.0.0.1",
  "port": 5557
}
```

where:

- **protocol**: Zero MQ transport protocol
- **ip**: ip v4 address
- **port**: ip port number

## Task types

The values for source_endpoint and sink_endpoint determines the different task types:

- **END**: in this case only the source_endpoint is specified, so the sink_endpoint has a null value. This kind of task is generally an end task, because only reads from the source queue but do not send anything to an output queue.
- **STARTER**: in this case only the sink_endpoint is specified and the source_endpoint has a null value. This kind of task is generally a starting task because does not read from any source queue and only writes to the output queue.
- **MIDDLE**: in this case, both the source_endpoint and the sink_endpoint will have values. This is generally a middle task, because reads from an input queue and writes to an output queue.

**business**: Business logic specification. Has the following structure

```json
  "business": {
    "module": "Test.Lib.PipelineManager.Business",
    "class": "Business1",
    "worker": "perform_any_calculation",
    "instance_parameters": {}
  }
```

where:

- **module**: namespace pointing to the class container module
- **class**: name of the class that implements the method to be executed
- **worker**: the member of the class to be executed
- **instance_parameters**: parameters required for the class constructor

# Setting up the task list

The task list specifies the task sequence and the amount of parallel instances of each task will be executed.

The task list has the following format.

```json
{
  "task_list": [
    {
      "task_id": "task_1",
      "task_config": "task_1.json",
      "instances": 1
    },
    {
      "task_id": "task_2",
      "task_config": "task_2.json",
      "instances": 3
    },
    {
      "task_id": "task_3",
      "task_config": "task_3.json",
      "instances": 3
    }
  ],
  "execution_order": "reverse"
}
```

where:

**task_id**: matches the task_id in the task specification.

**task_config**: specifies the task configuration file

**instances**: specify how many parallel instances of the task will be executed, each as a different process.

# Running The Pipeline

Finally to run the pipeline you need to execute from command line:

```bash
setlocal
set PYTHONPATH=<project_root_path>
CALL <python_virtual_env_path>Scripts\activate.bat
echo %1
python <project_root_path>Lib/PipelineManager/Manager.py <config_folder> <task_list_config>
CALL <python_virtual_env_path>deactivate.bat
endlocal
```

```bash
setlocal
set PYTHONPATH=C:/Users/mchiu/OneDrive/mch/Work/TheCompany/Development/src/python/mch/
CALL C:\mch_py_38\Scripts\activate.bat
echo %1
python C:/Users/mchiu/OneDrive/mch/Work/TheCompany/Development/src/python/mch/Lib/PipelineManager/Manager.py "./config/" "task_list.json"
CALL C:\mch_py_38\Scripts\deactivate.bat
endlocal
```

where:

<path_path>: is the root python path

<config_folder>: folder where the task list and task configuration files are located.

<task_list>: task list file name:

Example:

```bash
python /root/mch/Lib/PipelineManager/Manager.py "./config/" "task_list.json"
```

```
{
  "task_id": "task_1",
  "protocol": "tcp",
  "source_endpoint": null,
  "sink_endpoint": {"protocol": "tcp",
                    "ip": "127.0.0.1",
                    "port": 5557},
  "business": {
    "module": "Test.Lib.PipelineManager.Business",
    "class": "Business1",
    "worker": "perform_any_calculation",
    "instance_parameters": {}
  },
  "lifecycle": "infinite"
}
```

```
{
  "task_id": "task_1",
  "protocol": "tcp",
  "source_endpoint": null,
  "sink_endpoint": {"protocol": "tcp",
                    "ip": "127.0.0.1",
                    "port": 5557},
  "business": {
    "module": "Test.Lib.PipelineManager.Business",
    "class": "Business1",
    "worker": "perform_any_calculation",
    "instance_parameters": {}
  },
  "lifecycle": "infinite"
}
```

