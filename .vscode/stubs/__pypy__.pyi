# Stub file for PyPy-specific modules

class StringBuilder:
    def append(self, s: str) -> None: ...
    def build(self) -> str: ...

class builders:
    StringBuilder: type[StringBuilder]

# Add other PyPy-specific modules as needed