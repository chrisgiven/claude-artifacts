import time


def wait_for(desc, fn, timeout=120, interval=1.0):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if fn():
                return
        except Exception:
            pass
        time.sleep(interval)
    raise TimeoutError(f"timed out waiting for: {desc}")
