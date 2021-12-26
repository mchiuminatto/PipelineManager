setlocal
set PYTHONPATH=C:/Users/mchiu/OneDrive/mch/Work/TheCompany/Development/src/python/mch/
CALL C:\mch_py_38\Scripts\activate.bat
echo %1
python C:/Users/mchiu/OneDrive/mch/Work/TheCompany/Development/src/python/mch/Lib/PipelineManager/PipelineManager.py --config_folder="./config/" --config_file="task_1.json"
CALL C:\mch_py_38\Scripts\deactivate.bat
endlocal