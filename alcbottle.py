import inspect
import functools

class AlcBottle:
    name = 'alcbottle'
    api = 2

    def __init__(self, Session):
        self.Session = Session

    def apply(self, cb, route):
        signature = inspect.signature(cb)
        if 'session' not in signature.parameters:
            return cb

        @functools.wraps(cb)
        def wrapper(*args, **kwargs):
            with self.Session() as session:
                kwargs['session'] = session
                return cb(*args, **kwargs)

        return wrapper
