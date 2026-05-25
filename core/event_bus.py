class EventBus:
    def __init__(self):
        self._handlers = {}

    def on(self, event_name, handler):
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)

    def off(self, event_name, handler):
        if event_name in self._handlers:
            self._handlers[event_name] = [
                h for h in self._handlers[event_name] if h != handler
            ]

    def emit(self, event_name, **kwargs):
        results = []
        for handler in self._handlers.get(event_name, []):
            try:
                result = handler(**kwargs)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results

    def once(self, event_name, handler):
        def wrapper(**kwargs):
            self.off(event_name, wrapper)
            return handler(**kwargs)
        self.on(event_name, wrapper)

    def list_events(self):
        return {k: len(v) for k, v in self._handlers.items()}
