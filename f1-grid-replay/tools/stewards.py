"""Turn race-control messages into steward events: [t, [car numbers], kind, label, reason]."""
import re, datetime
def _t(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
def stewards(rc, T0):
    out = []
    for r in rc:
        m = r.get("message") or ""; t = round(_t(r["date"]) - T0, 1)
        nums = [int(n) for n in re.findall(r"(?:CARS?|AND) (\d+) \([A-Z]{3}\)", m)]
        if not nums:
            continue
        reason = ""
        parts = m.split(" - ")
        if len(parts) > 1 and "TRACK LIMITS" not in m:
            reason = parts[-1].strip().capitalize()
        kind = label = None
        if "DELETED" in m and "TRACK LIMITS" in m:
            kind = "TL"; tm = re.search(r"TURN (\d+)", m); label = "Lap time deleted" + (f" · T{tm.group(1)}" if tm else "")
        elif "PENALTY SERVED" in m:
            kind = "SERVED"; label = "Penalty served"
        elif "NO FURTHER" in m:
            kind = "NFA"; label = "No further action"
        elif "PENALTY" in m:
            kind = "PEN"
            if (x := re.search(r"(\d+) SECOND TIME PENALTY", m)): label = f"+{x.group(1)}s"
            elif (x := re.search(r"(\d+) SECOND STOP", m)): label = f"{x.group(1)}s stop-go"
            elif "DRIVE THROUGH" in m: label = "Drive-through"
            elif "STOP-AND-GO" in m or "STOP AND GO" in m: label = "Stop & go"
            elif "GRID" in m: label = "Grid penalty"
            else: label = "Penalty"
        elif "AFTER THE RACE" in m:
            kind = "POST"; label = "Investigated after race"
        elif "UNDER INVESTIGATION" in m:
            kind = "INV"; label = "Under investigation"
        elif "REPRIMAND" in m or "WARNING" in m:
            kind = "WARN"; label = "Reprimand" if "REPRIMAND" in m else "Warning"
        elif "BLACK AND WHITE" in m:
            kind = "BW"; label = "Black & white flag"
        elif "NOTED" in m:
            kind = "NOTED"; label = "Incident noted"
        if kind:
            if kind == "PEN": nums = nums[:1]
            out.append([t, nums, kind, label, reason])
    out.sort(key=lambda e: e[0])
    return out
