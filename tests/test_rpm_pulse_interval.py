import importlib.util
import sys
import types
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load_module(relative, stubs=None, name="tested_module"):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, stubs or {}):
        spec.loader.exec_module(module)
    return module


def settings_stubs():
    settings = types.ModuleType("openplotterSettings")
    for name in ("conf", "platform", "language"):
        setattr(settings, name, types.SimpleNamespace())
    return {"openplotterSettings": settings, "ujson": json}


def gpio_reader(gpio):
    stubs = settings_stubs()
    stubs.update(
        {
            "pigpio": types.ModuleType("pigpio"),
            "RPi": types.ModuleType("RPi"),
            "RPi.GPIO": gpio,
            "websocket": types.SimpleNamespace(create_connection=mock.Mock()),
        }
    )
    return load_module("openplotterGpio/openplotterGpioRead.py", stubs)


class RPMIntervalTest(unittest.TestCase):
    def test_two_pulses_per_revolution_give_steady_rpm(self):
        module = gpio_reader(mock.Mock())
        clock = [0.0]
        with (
            mock.patch.object(module.time, "time", side_effect=lambda: clock[0]),
            mock.patch.object(module.time, "monotonic", side_effect=lambda: clock[0]),
        ):
            reader = module.rpmReader(4, pulses_per_rev=2)
            for count in range(1, 5):
                clock[0] = count * 0.5
                reader.fell(4)
                self.assertAlmostEqual(reader.rpm, 60.0)
            self.assertEqual(reader.counter, 2)

    def test_rejected_short_pulse_does_not_move_interval(self):
        module = gpio_reader(mock.Mock())
        clock = [0.0]
        with (
            mock.patch.object(module.time, "time", side_effect=lambda: clock[0]),
            mock.patch.object(module.time, "monotonic", side_effect=lambda: clock[0]),
        ):
            reader = module.rpmReader(4)
            clock[0] = 0.005
            reader.fell(4)
            self.assertEqual(reader.counter, 0)
            clock[0] = 1.0
            reader.fell(4)
            self.assertAlmostEqual(reader.rpm, 60.0)


if __name__ == "__main__":
    unittest.main()
