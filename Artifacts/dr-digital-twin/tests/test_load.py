import time
import unittest

from drtwin.load import Load


class FakeClient:
    def call(self, method, path, timeout=None):
        return 200, {"site": "A"}


class LoadThread(unittest.TestCase):
    def test_stop_joins_cleanly(self):
        # Regression: the stop flag was named _stop, shadowing Thread._stop,
        # which Thread.join() calls on Python 3.12 -> "'Event' object is not callable".
        load = Load(FakeClient(), rate=200)
        load.start()
        time.sleep(0.05)
        load.stop()
        self.assertFalse(load.is_alive())
        self.assertTrue(load.records)
        self.assertTrue(all(r["ok"] for r in load.records))


if __name__ == "__main__":
    unittest.main()
