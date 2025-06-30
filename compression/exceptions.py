class KeyDontLoadException(Exception):
    def __init__(self):
        super().__init__("Cryptokey dont load!")