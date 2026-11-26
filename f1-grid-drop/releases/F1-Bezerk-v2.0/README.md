# F1 Bezerk v2.0 (realism upgrade, in progress)

- **v2.0 live page:** https://claude.ai/artifact/51RaQNnxXYXN9voVZQa2Vx (a new page with its own betting pool)
- **v1.0 is locked:** `../index.html` and `../releases/F1-Bezerk-v1.0/`, live at https://claude.ai/artifact/T78SFRzPEEh7yYV2BaSAXJ

## What's new in v2.0 (phase 1)

- **Real textures:** photo-scanned grass, rock, snow and asphalt from Poly Haven, all CC0 (free to use, no attribution required; credited here anyway):
  - Leafy Grass, Aerial Grass Rock, Rock Face 03, Snow 02 and Asphalt Track.
  - The grass keeps the course's green palette and adds the photo's detail.
  - Rock is mapped from three sides, so steep faces don't stretch.
  - Mountain textures blend by height and steepness.
- **Track:** real asphalt with grain, bumps and roughness, which shines when wet.
- **Real-sky reflections** on the cars, from the "Kloofendal 48d Partly Cloudy" sky photo by Poly Haven.
- **Smoother edges:** 4× multisampling with the glow on.
- **Soft contact shadows:** ambient occlusion, switched off first on slower computers before anything else is lowered.
- **Safe fallback:** if the textures don't load, the v1.0 look stays.
- **Size:** the textures are about 1.8 MB in `assets/`.

## v2.0 round 7

1. **Replays match the action:**
   - Each replay now starts about 2 seconds before the moment itself and ends about 2 seconds after.
   - It slows right down at the moment of impact, and frames both cars in a collision.
   - It shows a headline such as "Bottas is eaten by a T-rex".
   - The hosts talk about the replay while it plays (other commentary waits).
2. **Cars:**
   - Original team liveries painted on: a diagonal sweep, twin stripes or a dark fade, chosen per team in its own colours.
   - Lettering around the outer tyre walls.
   - Slotted rear-wing endplates and a raised floor edge.
3. **Sound (SOUND switch, key U):**
   - Everything is generated in the browser.
   - Wind rush that rises with speed, crash impacts scaled by how hard the hit was, and landing thumps.
   - Crowd noise near the grandstands, with a roar at the finish.
   - T-rex roars, rain, start-light beeps and firework pops.
4. **TV graphics:**
   - Live gaps to the leader in the running order and the full-screen standings.
   - Lower-third graphics: BATTLE FOR P2, NEW LEADER, and SPEED TRAP · FASTEST.
   - Full names on the podium.
5. **🎬 DIRECTOR camera (key 7):** cuts between cameras like TV:
   - the wide TV shot on the grid;
   - one side shot over each big drop;
   - onboard with the attacker in an overtake or with the chaser in a battle;
   - a varied mix of shots in between;
   - the TV camera, in slow motion, at the finish line.
6. **Replays on phones:** when the race screen plays a replay, phones in the cockpit view play the same moment in slow motion from an orbiting camera, with the headline, then return to the live view.

## v2.0 round 6

- **Progress page:** https://claude.ai/artifact/NoagHvUYA67fxdHe5G9syZ shows every round with before-and-after screenshots. It's also linked as "📈 What's new" under the race, and a copy is in `progress/`.
- **🏆 Championship mode:** from RACE SETUP, "START A 5-RACE CHAMPIONSHIP".
  - Each race gets a random setup, announced by the hosts.
  - F1 points (25, 18, 15, 12, 10, 8, 6, 4, 2, 1) and a standings table after every race.
  - After race 5, a "WORLD CHAMPION" ceremony with fireworks.
  - "THIS RACE" shows 🏆 RACE n/5.
  - The championship is saved in this browser.
- **Phones see the obstacles and creatures too:** the race screen sends which obstacles were chosen and streams their positions (wrecking ball, windmill, balls, pins, tyres, the T-rex crossing, the stampede herd and the pterodactyl). Phones only show them when their copy of the course matches exactly.
- **Lighter rendering:** about 3.6× fewer triangles per frame (4.25 million → 1.19 million):
  - Rocks simplified to about 320 triangles each.
  - The invisible shadow-casting trees use very simple shapes.
  - Lighter heads for the crowd.
- **Cars:** a team-colour stripe along the nose, a roll-hoop camera pod, and wheels at the real 2026 tyre size (about 72 cm).
- **Downloaded copy:**
  - Opened straight from disk, it now skips the textures (browsers block them in 3D from files) instead of risking a frozen screen.
  - The phone betting slip no longer waits forever: it explains why it can't connect and offers "▶ OPEN THE RACE INSTEAD".

## v2.0 round 5

- **Phone driver view (📺):**
  - The race screen broadcasts every car's position, rotation, speed and status about 6 times a second through the page's live room. Each message is under 1 KB; the platform limit is 4 KB.
  - Every 2 seconds it also sends the race setup: course, car order, giant car, weather and time of day.
  - On the betting slip, **📺 WATCH FROM …'S COCKPIT** opens a full-screen cockpit view of the driver you picked, with your position, speed and race time. ◀ ▶ switch drivers, and BACK TO SLIP returns.
  - The phone draws the same course and scenery itself, and smooths the motion between updates.
  - Everything the phone receives is checked before use.
  - Only the race screen (owner or Editor) can broadcast.
  - Not shown on phones yet: obstacles, dinosaurs and replays.
- **Cars:**
  - Wings use real aerodynamic profiles: rounded leading edge, thin trailing edge, cambered downwards.
  - Glossy carbon parts.
  - Helmets in the team's lighter colour.
  - The driver's code on both sides of the engine cover.
- **T-rex and raptors:**
  - One smooth body from tail tip to neck, with a sculpted head and jaw.
  - Muscular thighs and slim shins.
  - Pale bellies, dark backs, stripes and blotches.
- **Light towers:** steel lattice masts with zig-zag bracing and a bank of 12 floodlights each.
- **Grandstands:**
  - Fans with bodies, arms and heads in team-coloured shirts.
  - A roof frame.
  - Lit advertising boards.
  - Seven team-colour flags waving on the roof.
- **Long-necked dinosaurs:** rebuilt the same way as the T-rex: smooth body, neck, head and solid legs, with mottled skin.
- **Stampede balance:** the herd now gains on the last car more gently. In one test with the earlier, harder herd, only 3 of 22 finished.
- **Fixes:**
  - The four plant kinds were sharing one compiled shader on the graphics card, so the grass was drawn at fir-tree size. Each kind now has its own.
  - The grass is now knee-high, as intended.

## v2.0 round 4: real scanned nature

All from Poly Haven 3D scans (CC0): Island Tree 02, Fir Sapling Medium, Searsia Lucida, Grass Medium 02, Boulder 01, Namaqualand Boulder 02 and Rock Moss Set 01.

- **Trees and bushes:**
  - Each scanned plant was photographed from 8 sides and from above into one image sheet (the "impostor" technique games use for forests).
  - In the game, each tree is a panel that turns to face the camera and shows the matching photo angle, switching to the top view when the camera looks straight down.
  - About 1,700 trees (firs higher up, leafy trees lower down) and 2,600 bushes.
- **Grass:** about 26,000 scanned grass clumps around the course, drawn only within about 75 m of the camera to protect speed.
- **Rocks:** the real scanned shapes, simplified from up to 180,000 polygons to about 2,200 each (5 shapes), wrapped in the scanned rock texture. They cast real shadows.
- **Colour:** the scans are photographed in shade and are naturally dark, so each kind of plant gets a colour lift to sunlit greens. The plants also darken at night and in the rain.
- **Shadows:** the earlier tree shapes still cast the tree shadows, invisibly.
- **Fallback:** if these files don't load, the earlier trees and rocks stay.
- **Size:** about 1.7 MB in total (four WebP image sheets, plus rocks.json and plants.json).

## v2.0 round 3

- **Redesign:**
  - The bar under the race now holds only START, RESET, RACE SETUP, RANDOMIZE, SPEED, SLOW-MO, COMMENTARY and REPLAYS.
  - A "THIS RACE" line shows the active setup as tags, with a "change" link.
  - Drop angle, grid order, time of day and every special feature are in RACE SETUP.
  - All keyboard shortcuts still work, listed under "Keyboard shortcuts".
- **Night race lighting:**
  - Darkness: dark surroundings under dim blue moonlight, a moon and stars.
  - Floodlights: the six towers nearest the action cast real light on the cars. Every tower lights a glowing pool on the track, with a faint beam under it.
  - Cars: each runs a red rear light, as real F1 cars do at night and in the rain (it flashes in the wet), with light trails behind it. The paint reflects the floodlights.
  - Crowd: camera flashes in the grandstand.

## v2.0 round 2

- **Cars:** sculpted bodywork instead of boxes: a tapered nose, a raised cockpit and airbox, sidepods that narrow towards the back, and a shark-fin engine cover. Tyres have rounded shoulders, and the paint is glossier, with stronger sky reflections.
- **Trees and ground cover:**
  - Conifers are built from five drooping, uneven tiers.
  - Broadleaf trees have leafy multi-lobed crowns, shaded darker underneath.
  - About 2,600 bushes and 900 boulders are scattered over the hills.
- **Water:** the lake has a moving, rippled surface that reflects the real sky.
- **Atmosphere:**
  - Soft, sunlit clouds.
  - Sun glare with lens ghosts when you look towards the sun.
  - Dust floating in the sunlight around the camera.
- **Faster fast-forward:** at 2× and above, the physics runs 60 steps a second instead of 120, which halves the work. In tests at 4×, races were stable (11 of 22 finished, the normal range).
- **RACE SETUP menu (⚙):**
  - Pick the drop, day or night, and any special features: chaos, stampede, showers, rain, turbo, moon, giant car, backwards and kicker jump.
  - **🎲 RANDOMIZE** picks a fresh mix of 1 to 3 specials, plus random drop and time of day.
  - **SAVE & SET UP RACE** sets up the race. A NEXT RACE banner shows the mix, and Rex and Priya announce it.
  - **Surprise me every race** randomizes automatically each time you start the next race.
  - The last setup is remembered in this browser.
- **DRIVER button:** in the camera bar. It opens the driver view of the selected car, or of the leader. Clicking any car still works too.
- **LIVE pop-up:** now sits in the bottom-right corner, below the full-screen standings and above the driver view when that is open.

---

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

## Shared betting from phones

- **The race screen** (the owner's computer or TV) is the host. It opens betting for each race, locks picks at lights out, scores the race and keeps the leaderboard in the page's shared database. Only the owner or an Editor can write there.
- **Friends** open the page's link with `#bet` added to the end. That loads a light betting slip without the 3D race. They tap a driver, and the pick travels through the page's live room. They can change it until lights out.
- **Everyone sees** the live picks, the locked picks, the latest result and the leaderboard.
- **Race conditions on the slip:** the drop angle plus rain, showers, stampede, moon gravity, night, giant car, backwards and chaos, as tags. For rain and moon gravity, Rex and Priya add a short exchange, and a combined one when both are on. It updates live as the host changes settings. A 🔊 HEAR IT button reads the exchange aloud: Claude voices where the platform offers them (two different voices), otherwise the phone's own voices. Tap again to stop.
- **Cheering:** friends tap 👏 🔥 😱 🦖 or 🏁 on the slip. The emoji floats up the race screen with their name (or "A fan"). Only those five emoji are accepted, and names are shown as plain text.
- **Totals** carry over between races until the host presses NEW SESSION.
- **Requirements:** each friend needs a claude.ai account and an invitation to the page from the owner (Share menu, invite by email), and must be signed in. People arriving by a public link can't join the live room.
- **Fallback:** when the shared features aren't available, for example a downloaded copy of the page, the BETS tab falls back to pass-and-play on one screen.

## Betting pool (one screen) and season

- **BETS tab (pass-and-play):** add any number of players. Each picks a winner before the start; picks lock at lights out.
- **Scoring:** winner 10 points, podium (2nd or 3rd) 3 points, and double for a long shot (a driver who started 11th or lower).
- **Totals:** they carry over between races until you press **NEW SESSION**, which zeroes the points but keeps the names. LUCKY DIP picks for anyone who hasn't chosen.
- **SEASON tab:** F1 points (25, 18, 15, 12, 10, 8, 6, 4, 2, 1) and wins across races, with RESET SEASON. The SEASON grid order puts the points leader on pole.
- **Storage:** both are saved in this browser only, so they survive a reload but aren't shared with other devices. Resets need a second tap to confirm.

## More modes

- **SPEED (1×, 1.5×, 2×, 3×, 4×):** fast-forwards the whole race. Physics and results are unchanged. At 2× and above, only the biggest moments (cars eaten or snatched, off the mountain, wrecking ball) get a replay, and at most two, so the race isn't held up. If your computer can't run the physics fast enough, a "running 2.4×" note next to the buttons shows the real speed.
- **TURBO (T):** air drag cut to 35% and rolling resistance halved, so cars build far more speed. Expect more airtime and many more crashes: in a test with chaos on, 7 of 22 finished and the winner took 29.0 s.

- **RAIN (W):** falling rain, overcast sky, a shiny wet track, spray behind the cars and much less grip.
- **MOON (M):** one-sixth gravity and no air (so no drag and no slipstream). Floaty and slow.
- **GIANT (G):** one random car is 2.5× bigger and starts at the back.
- **SHOWERS (H):** the race starts dry. When the leader is halfway down, the rain arrives: the sky clouds over, the track turns wet and every car loses grip.
- **STAMPEDE (K):** a herd of three T. rexes and four raptors chases the field down the mountain, a few metres behind the last car still racing. Cars that slow down or crash get trampled, with a replay.

## LIVE pop-ups

- When something happens off-screen (a crash at the back, a car hit by an obstacle, big air), a LIVE window pops up in the top-right corner and shows it from an orbiting camera, with a headline such as "BOTTAS IS EATEN BY A T-REX".
- When a host talks about a car you can't see, the window cuts to that car while they speak.
- Commentary lines that are more than 3.5 seconds out of date are dropped, so the hosts talk about what is happening now.

## Monsters

- **Eaten:** in STAMPEDE mode, and with the T-rex crossing obstacle, a T-rex can grab a car in its jaws, shake it and throw it away. At most three cars per race. The driver is listed as EATEN.
- **Snatched:** in chaos mode, in about 6 races out of 10, a giant pterodactyl dives at a car in the middle of the pack and carries it off into the sky. The driver is listed as SNATCHED.

## Celebrations

- The winner does donuts on the run-off, with tyre smoke.
- Fireworks launch from the letters of the hillside sign, day and night.

## Records

- **RECORDS tab:** all-time bests: the fastest win for each drop angle, top speed, biggest air, closest finish, hardest hit and most crashes in one race. Each shows the driver, the date and the race settings.
- A **NEW RECORD** banner and a line from Priya when one is broken.
- Saved in this browser only. RESET RECORDS needs a second tap to confirm.

## Watching

- **Five cameras** (keys 1–5):
  - **TV** frames the leading group from the side; on a drop it moves down-range and looks back up the face.
  - **SIDE** fits the whole pack (every car within 90 m of the leader) from above and to the side.
  - **CHASE** follows a car from behind.
  - **CROW** flies behind and above the leader like a bird, gently swaying.
  - **DRONE** looks straight down on the pack, with the race running left to right, zooming out as the field spreads.
  - **GIANT** (key 6, giant mode only) puts you in the giant car's driver's seat, pitching and rolling with it. In giant mode the DRONE hovers over the giant car.
  - Every camera zooms with the mouse wheel, a pinch, or − / +.

- **Driver view:** pick a car (click it, or its row) to open a picture-in-picture window from that driver's cockpit. Close it with ✕.
- **Full screen:** shows a compact live top-12 running order on the right.
- **Colour:** a vibrance pass makes colours more vivid.

## Dinosaurs and wild animals

- **T. rex:** one roams near the course and roars as the leader goes past.
- **Long-necked dinosaurs:** three graze by the lake and on the hills.
- **Pterodactyls:** five circle over the course, flapping their wings.
- **Giraffes:** a family of three by the lake.
- **Deer:** a herd of seven in the fields.
- All of them wander and walk with animated legs.
- **Chaos obstacle:** a T. rex crossing the road, which cars can crash into, with a replay.

## Commentary

- Plain English throughout, with no racing jargon. When a racing trick comes up, the hosts explain it.
- About three times as many lines as before.
- A race update roughly every 10 seconds of race time: who leads and by how many metres, where on the mountain they are, the leader's speed, how many are still racing, the battle in the middle of the field, and the car in last place.

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

Space start · R reset · H showers · K stampede · 1–5 camera (TV, side, chase, crow, drone) · S slow-mo · D day/night · X chaos · C commentary · P replays · V backwards · + − zoom (or mouse wheel or pinch; each camera remembers its zoom) · F full screen · Esc deselect. The full-screen button sits next to the camera buttons; a START button stays on screen while in full screen. Click a car, or its row in the running order, to follow it.

## Tech

- One HTML file.
- three.js 0.160.0 (with its Sky, bloom and output add-ons) for 3D graphics and cannon-es 0.20.0 for physics, all pinned and loaded from jsDelivr through an import map.
- If the add-ons fail to load, the page falls back to the basic look.
- **Speed:** each car is merged into one painted mesh, one dark mesh and four wheel meshes, which cuts draw calls from about 1,500 to about 330 per frame with no visible change. Sharpness starts at 1.5× and rises to 2× on fast machines. The jumbotron skips drawing when it's off-screen, and cars that have stopped after the finish leave the physics simulation.
- **Backups:** `backups/` keeps a copy of the page from before the performance work.
- **Physics speed-up:** the course has about 880 fixed physics pieces. The stock physics engine compared every one of them with every other one on every step. The page now keeps them sorted along the course and checks each car only against the pieces near it, which made each physics step about 3.5 times faster in testing. A second change skips the costly contact test between a car's hull and a track piece when they are clearly apart, which made racing physics another 2.6 times faster.
- **No stutter:** if a slow computer can't keep up, the race runs slightly slower for a moment instead of freezing a frame.
- **Smooth motion:**
  - Cars are drawn between physics steps.
  - Sharpness lowers automatically on slow devices and rises again when there's headroom.
- No data is collected. The only thing stored is your day/night choice, in your own browser.
