import random
import string

ID_LENGTH = 8
CHARS = list(string.ascii_letters + string.digits)
for char in ["I", "l", "O", "0", "1"]:
    CHARS.remove(char)

FIRST_CHARS = list(string.ascii_letters)
for char in ["I", "l", "O"]:
    FIRST_CHARS.remove(char)


def gen_random_component_id() -> str:
    """Generate a random component ID that is a valid HTML ID without escaping."""
    first_char = random.choice(FIRST_CHARS)
    other_chars = "".join(random.choices(CHARS, k=ID_LENGTH - 1))
    return first_char + other_chars
