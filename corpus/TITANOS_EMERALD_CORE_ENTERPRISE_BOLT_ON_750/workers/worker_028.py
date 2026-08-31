"""Bounded stateless Emerald worker 028."""
def inspect(context=None):
    context=context or {}
    return {"worker":"worker_028","status":"READY","side_effects":False,"context_keys":sorted(context)}
if __name__=="__main__": print(inspect())
