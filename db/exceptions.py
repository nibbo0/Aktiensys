class PreviewRetrievalError(Exception):
    def __init__(self, message="Keine Vorschau vorhanden."):
        self.message = message
        super().__init__(self.message)
