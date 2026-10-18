#!/usr/bin/env python3
"""
OS PROCESS & CPU SCHEDULING SIMULATOR
=====================================
Enter processes (Process ID, Arrival Time, Burst Time, Priority) and the
program simulates six scheduling algorithms, showing for each one:
    Gantt chart, Completion Time, Turnaround Time, Waiting Time,
    Average Waiting Time, Average Turnaround Time
...then a COMPARISON screen ranking every algorithm on the same processes.

Priority convention: a HIGHER number means a HIGHER priority.

Run:  python3 cpu_scheduler.py          (menu)
      python3 cpu_scheduler.py --demo   (instant demo)

Formulas:  TAT = CT - AT        WT = TAT - BT
"""
import sys
from collections import deque

IDLE = "IDLE"
SAMPLE = [("P1", 0, 5, 2), ("P2", 1, 3, 4), ("P3", 2, 8, 1), ("P4", 3, 6, 3)]


def make(rows):
    """Build the process list from (pid, arrival, burst, priority) tuples.
    'i' keeps the original input order as a final tie-breaker."""
    return [{"pid": a, "at": b, "bt": c, "pr": d, "i": i}
            for i, (a, b, c, d) in enumerate(rows)]


# ============================================================== ALGORITHMS ==
# Each returns a timeline: a list of [label, start, end] slices.

def merge(tl):
    """Join neighbouring slices belonging to the same process."""
    out = []
    for lab, s, e in tl:
        if out and out[-1][0] == lab and out[-1][2] == s:
            out[-1][2] = e
        else:
            out.append([lab, s, e])
    return out


def nonpre(ps, key):
    """Engine for FCFS / SJF / Priority.
    Pick the best arrived process by `key`, then run it to completion."""
    t, tl, left = 0, [], list(ps)
    while left:
        ready = [p for p in left if p["at"] <= t]
        if not ready:                          # nothing arrived yet -> CPU idle
            nxt = min(p["at"] for p in left)
            tl.append([IDLE, t, nxt])
            t = nxt
            continue
        p = min(ready, key=key)
        tl.append([p["pid"], t, t + p["bt"]])
        t += p["bt"]
        left.remove(p)
    return merge(tl)


def pre(ps, key):
    """Engine for SRTF / Preemptive Priority.
    Re-decides who owns the CPU at every single time unit."""
    rem = {p["pid"]: p["bt"] for p in ps}
    t, tl, cur = 0, [], None
    while any(rem.values()):
        ready = [p for p in ps if p["at"] <= t and rem[p["pid"]]]
        if not ready:
            nxt = min(p["at"] for p in ps if rem[p["pid"]])
            tl.append([IDLE, t, nxt])
            t, cur = nxt, None
            continue
        # tie-break: criterion, then keep current process, then arrival, then input order
        p = min(ready, key=lambda x: (key(x, rem), x["pid"] != cur, x["at"], x["i"]))
        tl.append([p["pid"], t, t + 1])
        rem[p["pid"]] -= 1
        t += 1
        cur = p["pid"] if rem[p["pid"]] else None
    return merge(tl)


def rr(ps, q):
    """Round Robin. Processes arriving DURING a slice join the ready queue
    before the process that was just preempted goes to the back."""
    order = sorted(ps, key=lambda p: (p["at"], p["i"]))
    rem = {p["pid"]: p["bt"] for p in ps}
    tl, dq, t, i, done = [], deque(), 0, 0, 0

    def arrivals(now):                         # queue everyone who has arrived
        nonlocal i
        while i < len(order) and order[i]["at"] <= now:
            dq.append(order[i])
            i += 1

    arrivals(t)
    while done < len(ps):
        if not dq:                             # idle gap: jump to next arrival
            tl.append([IDLE, t, order[i]["at"]])
            t = order[i]["at"]
            arrivals(t)
            continue
        p = dq.popleft()
        run = min(q, rem[p["pid"]])
        tl.append([p["pid"], t, t + run])
        t += run
        rem[p["pid"]] -= run
        arrivals(t)
        if rem[p["pid"]]:
            dq.append(p)
        else:
            done += 1
    return merge(tl)


ALGOS = [
    ("FCFS",                  lambda ps, q: nonpre(ps, lambda p: (p["at"], p["i"]))),
    ("SJF (non-preemptive)",  lambda ps, q: nonpre(ps, lambda p: (p["bt"], p["at"], p["i"]))),
    ("SRTF (preemptive SJF)", lambda ps, q: pre(ps, lambda p, r: r[p["pid"]])),
    ("Priority",              lambda ps, q: nonpre(ps, lambda p: (-p["pr"], p["at"], p["i"]))),
    ("Priority (preemptive)", lambda ps, q: pre(ps, lambda p, r: -p["pr"])),
    ("Round Robin",           lambda ps, q: rr(ps, q)),
]


# ================================================================= METRICS ==

def metrics(ps, tl):
    """-> {pid: (completion, turnaround, waiting)}"""
    out = {}
    for p in ps:
        ct = max(s[2] for s in tl if s[0] == p["pid"])
        tat = ct - p["at"]
        out[p["pid"]] = (ct, tat, tat - p["bt"])
    return out


# ================================================================= DISPLAY ==

def cell(v, width):
    """Numbers right-aligned, text left-aligned."""
    s = str(v)
    return " " + s.ljust(width - 1) if s[:1] and not s[0].isdigit() \
        else s.rjust(width - 1) + " "


def table(hdr, rows):
    """Draw a box table sized to its contents."""
    w = [max(len(str(r[i])) for r in [hdr] + rows) + 2 for i in range(len(hdr))]
    line = lambda l, m, r: l + m.join("-" * x for x in w) + r          # noqa: E731
    out = [line("+", "+", "+"),
           "|" + "|".join(str(h).center(x) for h, x in zip(hdr, w)) + "|",
           line("+", "+", "+")]
    out += ["|" + "|".join(cell(v, x) for v, x in zip(r, w)) + "|" for r in rows]
    out.append(line("+", "+", "+"))
    return "\n".join(out)


def gantt(tl, maxw=76):
    """Draw the Gantt chart with a time ruler underneath.
    Each slice is sized to its duration; long schedules wrap onto more lines."""
    w = [max(len(s[0]) + 2, (s[2] - s[1]) * 2) for s in tl]
    out, i = [], 0
    while i < len(tl):
        row, used = [], 1                      # collect slices that fit a line
        while i < len(tl) and (not row or used + w[i] + 1 <= maxw):
            used += w[i] + 1
            row.append(i)
            i += 1
        ws = [w[k] for k in row]
        edge = "+" + "+".join("-" * x for x in ws) + "+"
        mid = "|" + "|".join(tl[k][0].center(x) for k, x in zip(row, ws)) + "|"
        ruler, pos = "", 0
        for k, x in zip(row, ws):              # put each start time at its edge
            ruler = (ruler + " " if len(ruler) > pos else ruler).ljust(pos) \
                + str(tl[k][1])
            pos += x + 1
        ruler = (ruler + " " if len(ruler) > pos else ruler).ljust(pos) \
            + str(tl[row[-1]][2])
        out += [edge, mid, edge, ruler]
    return "\n".join(out)


def report(name, ps, tl):
    """Print one algorithm's full result. Returns (avg WT, avg TAT)."""
    m, n = metrics(ps, tl), len(ps)
    awt = sum(m[p["pid"]][2] for p in ps) / n
    atat = sum(m[p["pid"]][1] for p in ps) / n
    print(f"\n{'=' * 64}\n  {name}\n{'=' * 64}\n\n  GANTT CHART")
    print(gantt(tl))
    print(table(["PID", "AT", "BT", "Prio", "CT", "TAT", "WT"],
                [[p["pid"], p["at"], p["bt"], p["pr"], *m[p["pid"]]] for p in ps]))
    print(f"  Average Waiting Time    = {awt:.2f}   "
          f"({' + '.join(str(m[p['pid']][2]) for p in ps)}) / {n}")
    print(f"  Average Turnaround Time = {atat:.2f}   "
          f"({' + '.join(str(m[p['pid']][1]) for p in ps)}) / {n}")
    return awt, atat


def compare(ps, q):
    """Run every algorithm, then show the comparison screen."""
    res = []
    for name, fn in ALGOS:
        label = f"{name} (quantum={q})" if name == "Round Robin" else name
        res.append((label, *report(label, ps, fn(ps, q))))

    print(f"\n{'=' * 64}\n  COMPARISON - same processes, six algorithms\n{'=' * 64}")
    best = min(r[1] for r in res)
    ranked = sorted(res, key=lambda r: r[1])
    print(table(["Rank", "Algorithm", "Avg WT", "Avg TAT", ""],
                [[i, nm, f"{w:.2f}", f"{ta:.2f}", "<-- BEST" if w == best else ""]
                 for i, (nm, w, ta) in enumerate(ranked, 1)]))

    peak = max(r[1] for r in res) or 1
    print("\n  AVERAGE WAITING TIME")
    for nm, w, _ in res:
        print(f"    {nm:<24}|{'#' * round(w / peak * 32):<32} {w:6.2f}"
              + ("  <-- BEST" if w == best else ""))

    win, lose = ranked[0], ranked[-1]
    print(f"\n  Winner : {win[0]} - lowest average waiting time ({win[1]:.2f})")
    print(f"  Worst  : {lose[0]} ({lose[1]:.2f})")
    if lose[1]:
        print(f"  Picking the winner saves {lose[1] - win[1]:.2f} time units of "
              f"waiting per process ({(lose[1] - win[1]) / lose[1] * 100:.0f}% better).")
    print("\n  Note: SJF/SRTF usually win on paper, but a real OS cannot know a\n"
          "  process's burst time in advance - so real systems use Round Robin.")


# ==================================================================== MENU ==

def main():
    ps, q = [], 2
    if "--demo" in sys.argv:
        compare(make(SAMPLE), q)
        return

    while True:
        print(f"\n{'=' * 64}\n  OS PROCESS & CPU SCHEDULING SIMULATOR\n{'=' * 64}")
        print(f"  Processes loaded: {len(ps)}     Round Robin quantum: {q}\n")
        print("   1. Add a process         4. Set time quantum")
        print("   2. Load sample data      5. RUN ALL + COMPARISON")
        print("   3. Show processes        0. Exit")
        ch = input("\n  Choice: ").strip()

        if ch == "1":
            try:
                pid = input("  Process ID: ").strip() or f"P{len(ps) + 1}"
                if any(p["pid"] == pid for p in ps):
                    print("  ! That Process ID already exists.")
                    continue
                at = int(input("  Arrival time: "))
                bt = int(input("  Burst time  : "))
                pr = int(input("  Priority (higher number = higher priority): "))
                if at < 0 or bt <= 0:
                    raise ValueError
                ps.append({"pid": pid, "at": at, "bt": bt, "pr": pr, "i": len(ps)})
                print(f"  Added {pid}.")
            except ValueError:
                print("  ! Invalid - use whole numbers, arrival >= 0 and burst > 0.")
        elif ch == "2":
            ps = make(SAMPLE)
            print(f"  Loaded {len(ps)} sample processes.")
        elif ch == "3":
            print(table(["PID", "AT", "BT", "Prio"],
                        [[p["pid"], p["at"], p["bt"], p["pr"]] for p in ps])
                  if ps else "  No processes yet.")
        elif ch == "4":
            try:
                q = max(1, int(input("  Time quantum: ")))
            except ValueError:
                print("  ! Enter a whole number.")
        elif ch == "5":
            compare(ps, q) if ps else print("  ! Add processes first (option 1 or 2).")
        elif ch == "0":
            print("  Goodbye!")
            return
        else:
            print("  ! Unknown option.")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n  Goodbye!")
