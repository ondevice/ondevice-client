import logging
import threading

class BackgroundThread():
    """ Thin wrapper around threading.Thread with simple event support.

    During the lifecycle of a backgrond thread the following events may occur (roughly in that order):
    - started: after a call to start()
    - running: before target() is being executed
    - stopping: after a call to stop()
    - finished: after target() has finished
    """
    def __init__(self, target, stopFn):
        self.target = target
        self.stopFn = stopFn
        self._listeners = {}
        self._thread = threading.Thread(target=self.run)

    def _emit(self, event, *args, **kwargs):
        listeners = list(self._listeners[event]) if event in self._listeners else []
        logging.info("thread {0} fired event: {1} (args={2}, kwargs={3}, {4} listeners)".format(self.target, event, args, kwargs, len(listeners)))

        for l in listeners:
            l(*args, **kwargs)

    def run(self):
        """ Runs the target function (don't call this directly unless you want the target function be run in the current thread) """
        self._emit('running')
        self.target()
        self._emit('finished')

    def addListener(self, event, fn):
        if event not in ['started', 'running', 'stopping', 'finished']:
            raise KeyError("Unsupported event: '{0}'".format(event))
        if not event in self._listeners:
            self._listeners[event] = set()

        self._listeners[event].add(fn)

    def addListenerObject(self, obj):
        fns = {'threadStarted': 'started', 'threadRunning':'running', 'threadStopping':'stopping', 'threadFinished':'finished'}
        for fn,event in fns.items():
            if hasattr(obj, fn):
                self.addListener(event, getattr(obj, fn))

    def removeListener(event, fn):
        if event not in self._listeners:
            return # Cant' remove something that isn't there
        self._listeners[event].remove(fn)

    def start(self):
        self._thread.start()
        self._emit('started')

    def stop(self):
        self.stopFn()
        self._emit('stopping')


class FixedDelayTask(BackgroundThread):
    """ Represents a repeating task that runs with a fixed delay (delay)
    in a background thread """

    def __init__(self, target, interval, *args, **kwargs):
        self._target = target
        self.interval = interval
        self.args = args
        self.kwargs = kwargs
        self._event = threading.Event()
        BackgroundThread.__init__(self, self._run, self._stop)

    def _run(self):
        while not self._event.wait(self.interval):
            try:
                self._target(*self.args, **self.kwargs)
            except:
                logging.exception('Exception in FixedDelayTask')

    def _stop(self):
        self._event.set()
