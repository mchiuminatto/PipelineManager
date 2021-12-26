from TestBase import TestBase
from Manager import Manager

class Test(TestBase):

    def test_case_1(self):
        """
        Test startup
        :return:
        """
        _manager = Manager("./config/", "task_list.json")
        _manager.startup()
        print("Task list to process \n", _manager.proc_table)


    def test_case_2(self):
        """
        Test startup
        :return:
        """
        _manager = Manager("./config/", "task_list.json")
        _manager.startup()
        _manager.spawn_tasks()


    def test_case_3(self):
        """
        Test startup
        :return:
        """
        _manager = Manager("./config/", "task_list.json")
        _manager.handler()


if __name__ == "__main__":
    _test=Test()
    _test.run([3])