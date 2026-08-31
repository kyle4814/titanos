from .state import canonical,sha
from .rail import rank
def run():
    assert canonical({"b":1,"a":2})=='{"a":2,"b":1}'
    assert sha({"x":1})==sha({"x":1})
    assert rank([{"priority":1,"created_at":1,"task_id":"a"},{"priority":2,"created_at":2,"task_id":"b"}])[0]["task_id"]=="b"
if __name__=="__main__": run(); print("OK")
