import unittest

from drtwin.measure import grade, measure


def recs(pattern, start=-2.0, gap=0.1):
    """pattern: string of '1' (ok) / '0' (fail), one char per write."""
    return [{"seq": i + 1, "t": start + i * gap, "ok": c == "1", "site": "A"} for i, c in enumerate(pattern)]


class Measure(unittest.TestCase):
    def test_transparent_failover_is_zero_rto(self):
        r = recs("1" * 50)
        m = measure(r, 0.0, {x["seq"] for x in r})
        self.assertEqual(m["rto_s"], 0.0)
        self.assertEqual(m["rpo_s"], 0.0)

    def test_rto_is_start_of_stable_success(self):
        # 20 ok before t0, outage of 30 writes, then recovery; a lone success
        # mid-outage must not count as recovery.
        r = recs("1" * 20 + "0" * 10 + "1" + "0" * 19 + "1" * 20)
        m = measure(r, 0.0, {x["seq"] for x in r})
        self.assertAlmostEqual(m["rto_s"], 3.0, places=1)
        self.assertEqual(m["failed_requests"], 29)

    def test_never_recovered(self):
        r = recs("1" * 20 + "0" * 30)
        m = measure(r, 0.0, {x["seq"] for x in r})
        self.assertIsNone(m["rto_s"])
        self.assertFalse(grade(m, {"rto_s": 60, "rpo_s": 0})["rto_pass"])

    def test_rpo_counts_lost_acknowledged_writes(self):
        r = recs("1" * 40 + "0" * 10 + "1" * 20)
        surviving = {x["seq"] for x in r} - set(range(11, 21))  # writes 11-20 lost
        m = measure(r, 0.0, surviving)
        self.assertEqual(m["lost_acked_writes"], 10)
        self.assertAlmostEqual(m["rpo_s"], 1.0, places=1)  # last kept #10 -> last lost #20

    def test_rpo_when_nothing_before_loss_survived(self):
        r = recs("1" * 10 + "0" * 5 + "1" * 10)
        surviving = {x["seq"] for x in r} - set(range(1, 11))
        m = measure(r, 0.0, surviving)
        self.assertAlmostEqual(m["rpo_s"], 0.9, places=1)


if __name__ == "__main__":
    unittest.main()
