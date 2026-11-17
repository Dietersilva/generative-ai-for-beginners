# F1 Bezerk

A private, fan-made 3D soapbox race. The 22 cars of the 2026 F1 grid race down a mountain course of about 0.9 km with no engines. Two fictional hosts call the race live, and real-time physics decides the result. It is a companion to Grid Replay, the replay page on the `claude/optimistic-dirac-orjjnb` branch.

**Every race is a new simulation.** It does not replay real results. Real data used:

- Driver names, teams and team colours, from Grid Replay's `season.json`.
- The grid order, from the 2026 drivers' standings after the São Paulo GP.

Fan-made and not affiliated with Formula 1.

## The course, top to bottom

1. The grid, on a 12° slope.
2. The big drop: 50°, 72° or 88°, falling 64 m.
3. The long fast downhill, with an optional kicker jump and a ski-jump landing hill.
4. A beach-ball zone (chaos mode).
5. The second drop: 22°, over a wide crest.
6. Four rollers.
7. The run to the finish, with giant bowling pins 60 m before the line (chaos mode).
8. Grandstands, the finish line and a jumbotron.

A typical race takes 30 to 40 seconds.

## What decides the race

- A random push start, reaction time and small setup differences in drag and rolling resistance.
- Slipstream: up to 45% less drag up to 25 m behind another car.
- Drivers steer, keep off the walls and pull out to overtake.
- **Chaos mode** (on by default) adds:
  - Driver mistakes.
  - Messy launches off the drops.
  - Bouncier contact between cars.
  - A random four of seven obstacles each race, announced by the hosts at the start: giant beach balls, giant bowling pins, runaway monster tyres, a crazy-golf windmill, traffic cones, a wrecking ball and a hay bale slalom.
- **Backwards mode:** every car races the whole course backwards. Drivers steer with the leading (rear) wheels, which keeps the cars stable.
- **Off the mountain:** cars that clear the barrier tumble down the solid mountainside.
- Marshals lift crashed cars clear after a few seconds.
- Like F1, the race closes 15 seconds after the winner finishes. Cars still running are listed as DNF.

## Instant replays

- Flips, cars going off the mountain, wrecking-ball and windmill hits, runaway tyres, big crashes, bowling strikes and big air get a slow-motion replay.
- Each replay opens with a swipe transition and plays in cinematic letterbox with an orbiting camera, while the hosts react.
- The race pauses during a replay, so you don't miss anything.
- Up to four replays per race, none in the final 130 m.
- After the race, **HIGHLIGHTS** replays the big moments and the finish.
- Skip a replay with SKIP, Space or Enter.

## Commentary

- **The hosts:** Rex Holloway (play-by-play) and Priya Vance (analyst) are fictional. They call the start, the drops, jumps, crashes, lead changes, the speed trap, bowling strikes and the finish, with on-screen captions.
- **The voices:** the speech uses voices built into your device, so they sound different on Windows, Mac, Android and iPhone.
- **If speech isn't available,** the captions still show.

## Scenery and effects

- **Terrain:** generated rolling hills and mountains, with grass, rock and snow.
- **Day:** a physically based sky with sun haze, clouds, and forests of conifer and broadleaf trees.
- **Night:** floodlights, stars and fireworks.
- **Landmarks:** a lake with a giant rubber duck, a hillside "F1 BEZERK" sign, wind turbines, hot-air balloons, a blimp and a TV helicopter that follows the leader.
- **At the finish:** a speed trap board, a jumbotron with a live chase camera, and a crowd that jumps as cars pass.
- **Effects:** sparks, dust, confetti, camera shake, and a soft glow on lights and fireworks.
- **Cars:** clear-coat paint that reflects the sky, multi-element wings, mirrors, tyre markings and wheel spokes.
- **Track:** textured asphalt.

## Controls

Space start · R reset · 1 2 3 camera (TV, side, chase) · S slow-mo · D day/night · X chaos · C commentary · P replays · V backwards · + − zoom (or mouse wheel or pinch; each camera remembers its zoom) · F full screen · Esc deselect. The full-screen button sits next to the camera buttons; a START button stays on screen while in full screen. Click a car, or its row in the running order, to follow it.

## Tech

- One HTML file.
- three.js 0.160.0 (with its Sky, bloom and output add-ons) for 3D graphics and cannon-es 0.20.0 for physics, all pinned and loaded from jsDelivr through an import map.
- If the add-ons fail to load, the page falls back to the basic look.
- **Smooth motion:**
  - Cars are drawn between physics steps.
  - Sharpness lowers automatically on slow devices and rises again when there's headroom.
- No data is collected. The only thing stored is your day/night choice, in your own browser.
