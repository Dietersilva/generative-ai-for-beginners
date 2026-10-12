import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from pixelrace.demo import DemoRace
from pixelrace.font import _GLYPHS, GLYPH_H, GLYPH_W, text_width
from pixelrace.model import CarState, Status
from pixelrace.render import LAYOUTS, Renderer, gap_label, race_times, start_lights
from pixelrace.timelapse import LAYOUTS as TL_LAYOUTS
from pixelrace.timelapse import TimelapseRenderer, finish_label, format_race_time, soft_ranks
from pixelrace.video import write_mp4


class FontTest(unittest.TestCase):
    def test_glyphs_are_3x5(self):
        for ch, rows in _GLYPHS.items():
            self.assertEqual(len(rows), GLYPH_H, ch)
            for row in rows:
                self.assertEqual(len(row), GLYPH_W, ch)
                self.assertTrue(set(row) <= {"#", "."}, ch)

    def test_text_width(self):
        self.assertEqual(text_width(""), 0)
        self.assertEqual(text_width("A"), 3)
        self.assertEqual(text_width("LAP"), 11)


class DemoRaceTest(unittest.TestCase):
    def setUp(self):
        self.race = DemoRace(seed=7, laps=20)

    def test_same_seed_same_race(self):
        other = DemoRace(seed=7, laps=20)
        self.assertEqual(self.race.end_time, other.end_time)
        self.assertEqual(self.race.state_at(900.0), other.state_at(900.0))

    def test_every_moment_is_ordered_and_consistent(self):
        race = self.race
        for i in range(201):
            t = race.end_time * i / 200
            states = race.state_at(t)
            self.assertEqual(len(states), len(race.drivers))
            self.assertIsNone(states[0].gap)
            self.assertNotEqual(states[0].status, Status.RETIRED)
            running = [s for s in states if s.status is not Status.RETIRED]
            retired = [s for s in states if s.status is Status.RETIRED]
            self.assertEqual(states, running + retired, "retired cars go to the back")
            for s in running[1:]:
                self.assertGreaterEqual(s.gap, 0.0)
                self.assertLessEqual(s.distance, running[0].distance + 1e-9)

    def test_finish(self):
        final = self.race.state_at(self.race.end_time)
        winner = final[0]
        self.assertEqual(winner.status, Status.FINISHED)
        self.assertEqual(winner.distance, 20)
        self.assertEqual(sum(s.status is Status.RETIRED for s in final), 1)
        for s in final:
            self.assertIn(s.status, (Status.FINISHED, Status.RETIRED))

    def test_cars_pit(self):
        seen = set()
        for i in range(2001):
            for s in self.race.state_at(self.race.end_time * i / 2000):
                if s.status is Status.PIT:
                    seen.add(s.code)
        self.assertGreaterEqual(len(seen), 8)

    def test_tyres_and_fastest_lap(self):
        for i in range(101):
            states = self.race.state_at(self.race.end_time * i / 100)
            for s in states:
                self.assertIn(s.compound, ("S", "M", "H"))
                self.assertGreaterEqual(s.tyre_age, 0)
            holders = sum(s.fastest_lap for s in states)
            self.assertLessEqual(holders, 1)
        self.assertEqual(sum(s.fastest_lap for s in self.race.state_at(self.race.end_time)), 1)

    def test_finish_times(self):
        final = self.race.state_at(self.race.end_time)
        times = [s.finish_time for s in final if s.status is Status.FINISHED]
        self.assertEqual(times, sorted(times))
        self.assertEqual(max(times), self.race.end_time)

    def test_rejects_tiny_race(self):
        with self.assertRaises(ValueError):
            DemoRace(laps=2)


class RenderTest(unittest.TestCase):
    def setUp(self):
        self.race = DemoRace(seed=3, laps=10)

    def test_frame_sizes(self):
        for name, layout in LAYOUTS.items():
            r = Renderer(self.race, layout=name, follow="AXL")
            for t in (0.0, self.race.end_time / 2, self.race.end_time):
                self.assertEqual(r.frame(t).size, layout.size)

    def test_frames_are_deterministic(self):
        a = Renderer(self.race).frame(400.0, 3).tobytes()
        b = Renderer(DemoRace(seed=3, laps=10)).frame(400.0, 3).tobytes()
        self.assertEqual(a, b)

    def test_rejects_unknown_driver_and_layout(self):
        with self.assertRaises(ValueError):
            Renderer(self.race, follow="ZZZ")
        with self.assertRaises(ValueError):
            Renderer(self.race, layout="square")

    def test_gap_labels(self):
        def car(status=Status.RUNNING, gap=1.234, laps=0):
            return CarState("AXL", 0, 0, 1.0, status, gap, laps)

        self.assertEqual(gap_label(car(gap=None), 1), "LEADER")
        self.assertEqual(gap_label(car(Status.FINISHED, gap=None), 1), "WINNER")
        self.assertEqual(gap_label(car(), 2), "+1.2")
        self.assertEqual(gap_label(car(laps=1), 5), "+1 LAP")
        self.assertEqual(gap_label(car(laps=2), 5), "+2 LAPS")
        self.assertEqual(gap_label(car(Status.PIT), 3), "PIT")
        self.assertEqual(gap_label(car(Status.RETIRED, gap=None), 9), "OUT")

    def test_race_times(self):
        times = race_times(self.race, duration=10, fps=30, hold=2)
        self.assertEqual(len(times), 360)
        self.assertEqual(times[0], self.race.start_time)
        self.assertEqual(times[299], self.race.end_time)
        self.assertEqual(times[-1], self.race.end_time)
        self.assertEqual(times, sorted(times))


class TimelapseTest(unittest.TestCase):
    def setUp(self):
        self.race = DemoRace(seed=3, laps=10)

    def test_frame_sizes_through_the_race(self):
        for name, layout in TL_LAYOUTS.items():
            r = TimelapseRenderer(self.race, layout=name, follow="CRU")
            for i in range(41):
                self.assertEqual(r.frame(self.race.end_time * i / 40, i).size, layout.size)
            self.assertEqual(r.frame(0.0, 0, lights=3).size, layout.size)

    def test_frames_are_deterministic(self):
        a = TimelapseRenderer(self.race).frame(400.0, 3).tobytes()
        b = TimelapseRenderer(DemoRace(seed=3, laps=10)).frame(400.0, 3).tobytes()
        self.assertEqual(a, b)

    def test_rejects_unknown_driver(self):
        with self.assertRaises(ValueError):
            TimelapseRenderer(self.race, follow="ZZZ")

    def test_soft_ranks(self):
        def car(code, d, status=Status.RUNNING):
            return CarState(code, 0, 0, d, status, None)

        apart = soft_ranks([car("A", 5.0), car("B", 4.9), car("C", 4.8)])
        for got, want in zip(apart, (0, 1, 2)):
            self.assertAlmostEqual(got, want, places=6)
        side_by_side = soft_ranks([car("A", 5.0), car("B", 5.0), car("C", 4.0)])
        self.assertAlmostEqual(side_by_side[0], 0.5)
        self.assertAlmostEqual(side_by_side[1], 0.5)
        mixed = soft_ranks([car("A", 10, Status.FINISHED), car("B", 9.5), car("C", 3, Status.RETIRED)])
        self.assertEqual(mixed, [0.0, 1.0, 2.0])

    def test_labels(self):
        self.assertEqual(format_race_time(1805.2155), "30:05.216")
        self.assertEqual(format_race_time(5400.5), "1:30:00.500")
        winner = CarState("A", 0, 0, 10, Status.FINISHED, None, finish_time=905.0)
        self.assertEqual(finish_label(winner, 1, 0.0), "15:05.000")
        second = CarState("B", 0, 0, 10, Status.FINISHED, 1.8784)
        self.assertEqual(finish_label(second, 2, 0.0), "+1.878")
        lapped = CarState("C", 0, 0, 9, Status.FINISHED, 95.0, 1)
        self.assertEqual(finish_label(lapped, 3, 0.0), "+1 LAP")

    def test_start_lights(self):
        lights = start_lights(fps=10, seconds=2.4)
        self.assertEqual(len(lights), 24)
        self.assertEqual(lights[0], 1)
        self.assertEqual(max(lights), 5)
        self.assertEqual(lights[-1], 0)
        self.assertEqual(lights[:20], sorted(lights[:20]))


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "needs ffmpeg")
class VideoTest(unittest.TestCase):
    def test_writes_scaled_mp4(self):
        race = DemoRace(seed=1, laps=5)
        r = Renderer(race, layout="portrait")
        times = race_times(race, duration=0.5, fps=10, hold=0)
        with tempfile.TemporaryDirectory() as tmp:
            old = os.getcwd()
            os.chdir(tmp)
            try:
                # A name that starts with "-" must not be read as an ffmpeg option.
                write_mp4((r.frame(t, i) for i, t in enumerate(times)), Path("-clip.mp4"), r.size, 10, 2)
                out = Path(tmp, "-clip.mp4")
                self.assertTrue(out.exists())
            finally:
                os.chdir(old)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "stream=width,height,nb_frames",
                 "-of", "csv=p=0", str(out)],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(probe.stdout.strip(), "360,640,5")


if __name__ == "__main__":
    unittest.main()
