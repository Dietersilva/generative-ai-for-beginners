# Grid Drop 2026

A private, fan-made 3D soapbox race. The 22 cars of the 2026 F1 grid roll down a far-too-steep ramp with no engines, and real-time physics decides the result. It is a companion to Grid Replay, the replay page on the `claude/optimistic-dirac-orjjnb` branch.

**Every race is a new simulation.** It does not replay real results. Real data used:

- Driver names, teams and team colours, from Grid Replay's `season.json`.
- The grid order, from the 2026 drivers' standings after the São Paulo GP.

Fan-made and not affiliated with Formula 1.

## What decides the race

- A random push start for each car (0.6 to 3.0 m/s) and a random reaction delay of up to 0.22 s.
- Small random differences in drag (±12%) and rolling resistance between cars.
- Slipstream: a car up to 25 m behind another has up to 45% less drag.
- Drivers steer straight, keep off the walls and pull out to overtake when blocked.
- Crashes, airtime, the kicker jump and collisions between cars.

## Controls

| Control | What it does |
| --- | --- |
| Ramp | Steep 50°, Too steep 72° or Cliff 88°. The drop is 64 m in every case |
| Grid | Championship order, reverse order or random |
| Time | Day (sky, clouds, hills, trees, crowd) or night (floodlights, stars, fireworks) |
| Kicker jump | Adds a 14° jump 72 m after the drop |
| Slow-mo | Runs the race at 30% speed |
| Camera | TV, side or chase. Click a car or a row in the running order to follow it |
| Keys | Space start · R reset · 1 2 3 camera · S slow-mo · D day/night · Esc deselect |

## Tech

- One HTML file.
- three.js 0.160.0 for 3D graphics and cannon-es 0.20.0 for physics, both pinned and loaded from jsDelivr.
- No data is collected. The only thing stored is your day/night choice, in your own browser.
