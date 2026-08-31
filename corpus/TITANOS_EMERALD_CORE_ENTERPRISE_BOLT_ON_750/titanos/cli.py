import argparse
from .doctor import run as doctor
from .queue import enqueue
from .rail import run_once
def main():
    p=argparse.ArgumentParser(prog="titanos"); s=p.add_subparsers(dest="cmd",required=True)
    s.add_parser("doctor"); q=s.add_parser("enqueue"); q.add_argument("mission"); q.add_argument("--priority",type=float,default=0); s.add_parser("run")
    a=p.parse_args()
    if a.cmd=="doctor": print(doctor())
    elif a.cmd=="enqueue": print(enqueue(a.mission,a.priority))
    else: print(run_once())
if __name__=="__main__": main()
