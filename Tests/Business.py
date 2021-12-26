class Business1:

    def __init__(self):
        self._process_count = 0

    def perform_any_calculation(self, *args, **params):
        _list_to_proc = None
        if self._process_count == 0:
            _list_to_proc = [{f"'id':{i}":f"'message':'sequence {i}'"} for i in range(0,5)]
            self._process_count += 1

        return _list_to_proc

class Business2:

    def __init__(self):
        pass

    def transform(self, *args, **kwargs):
        _payload = args[0]
        print("Business 2,  Received payload ", _payload)
        return _payload

class Business3:
    def __init__(self):
        pass

    def calculate(self, *args, **params):

        _message = args[0]
        print(f"Business 3 Processing {_message}")


