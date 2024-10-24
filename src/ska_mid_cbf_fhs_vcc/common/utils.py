import threading


class PollingService:
    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback
        self.timer = None
        self.is_running = False

    def _run(self):
        """Run the callback function and restart the timer."""
        if self.is_running:
            self.callback()
            self.timer = threading.Timer(self.interval, self._run)
            self.timer.start()

    def start(self):
        """Start the polling service."""
        if not self.is_running:
            self.is_running = True
            self._run()

    def stop(self):
        """Stop the polling service."""
        if self.timer is not None:
            self.timer.cancel()
        self.is_running = False
