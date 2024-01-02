from typing import List

MARK_WEIGHTS_SYMBOLS = {1: '\u00B9', 2: '\u00B2', 3: '\u00B3', 4: '\u2074', 5: '\u2075'}


async def parse_marks_from_lesson(marks) -> List[str]:
    return [
        {mark["value"]: mark["weight"]} for mark in marks
    ]
