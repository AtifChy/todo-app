from enum import IntEnum


class Priority(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    @classmethod
    def from_string(cls, value: str):
        if not isinstance(value, str):
            # Handle case where value is None or not a string
            return cls.NONE

        try:
            # Convert to uppercase to match enum names
            return cls[value.upper()]
        except KeyError:
            # If the string doesn't match any enum name, return NONE
            return cls.NONE

    def __str__(self):
        # Return the name of the enum in lowercase for display
        return self.name.lower()


PRIORITY_VALUES = [str(p) for p in Priority]
