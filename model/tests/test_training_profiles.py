import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from train import PROFILES


class TrainingProfileTests(unittest.TestCase):
    def test_cpu_pilot_is_small_and_cpu_only_profile(self):
        profile = PROFILES["cpu-pilot"]
        self.assertEqual(profile["steps"], 3000)
        self.assertLessEqual(profile["width"], 128)
        self.assertLessEqual(profile["layers"], 4)
        self.assertLessEqual(profile["context"], 128)
        self.assertEqual(profile["batch_size"], 4)

    def test_standard_profile_remains_separate(self):
        self.assertGreater(PROFILES["standard"]["steps"], PROFILES["cpu-pilot"]["steps"])


if __name__ == "__main__":
    unittest.main()
