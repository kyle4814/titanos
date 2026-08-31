from __future__ import annotations
import argparse
from .core import boot, enqueue, load_queue, pareto, execute_local, receipt

def main():
    p = argparse.ArgumentParser(prog="titanos")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("status")
    sub.add_parser("run")
    q = sub.add_parser("enqueue")
    q.add_argument("mission")
    q.add_argument("--priority", type=float, default=0.0)
    args = p.parse_args()

    if args.cmd == "doctor":
        print(boot())
        print({"queue_items": len(load_queue())})
    elif args.cmd == "status":
        print({"queue": len(load_queue())})
    elif args.cmd == "enqueue":
        print(enqueue(args.mission, args.priority))
    elif args.cmd == "run":
        boot()
        tasks = pareto(load_queue())
        if tasks:
            print(execute_local(tasks[0]))
        else:
            print({"status": "IDLE", "reason": "queue_empty"})

if __name__ == "__main__":
    main()
