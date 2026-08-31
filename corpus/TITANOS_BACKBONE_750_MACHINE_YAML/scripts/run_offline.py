from titanos.core import boot, enqueue, pareto, load_queue, execute_local
boot()
if not load_queue():
    enqueue("health", 100)
print(execute_local(pareto(load_queue())[0]))
