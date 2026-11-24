# check_pm.py
import dataclasses
from modules.process_manager.algorithms import (
    ProcessManager, SimulatedProcess, SchedulingAlgorithm as A)

def run(name, rows, algo, ts=2.0):
    procs = [SimulatedProcess(pid=p, arrival_time=a, burst_time=b) for p, a, b in rows]
    r = ProcessManager.simulate_multiprogramming(procs, algo, ts)
    print("\n==", name)
    for f in dataclasses.fields(r):
        v = getattr(r, f.name)
        if isinstance(v, list):
            for e in v:
                if hasattr(e, "event_type"):
                    print(f"  [{e.time:6.2f}] {e.process_id} {e.event_type} {e.details}")
        else:
            print(f"  {f.name}: {v}")

four = [("P1",0,8), ("P2",1,4), ("P3",2,6), ("P4",3,3)]
run("FCFS", four, A.FCFS)
run("SJF", four, A.SJF)
run("SRTF", four, A.SRTF)
run("RR q=2, staggered", four, A.ROUND_ROBIN)
run("RR q=2, all arrive at 0", [(p,0,b) for p,_,b in four], A.ROUND_ROBIN)
