import re
from enum import Enum
from pathlib import Path


class PartTypes(Enum):
    BASE = 0
    PROGRAM = 1
    CAPTURE = 2
    PICTURES = 3


class BidePart:
    type: PartTypes.BASE

    def __init__(self, file: Path, name: str, start: int, end: int, contents: str):
        self.file = file
        self.name = name
        self.start = start
        self.end = end
        self.contents = contents


class ProgramPart(BidePart):
    type: PartTypes.PROGRAM
    # todo: check re accuracy
    password_re = re.compile('#Password: ([A-Z]+)')


def parse_file(file: Path) -> list[BidePart]:
    parts = []
    lineno = 0

    name = ''
    start = 0
    contents_lines = []

    with open(file, encoding='utf-8') as f:
        while True:
            line = f.readline()
            if not line:
                # end of file
                break

            if not name:
                name = line.removeprefix('#Program name: ').removesuffix('\n')
                start = lineno
            elif line == '#End of part\n':
                contents = ''.join(contents_lines)
                p = ProgramPart(file, name, start, lineno, contents)
                parts.append(p)
                name = ''
            else:
                contents_lines.append(line)

            lineno += 1

    return parts


def main():
    file = Path('snake.bide')
    parts = parse_file(file)
    for p in parts:
        print(p)
        print(p.name)
        print(p.start)
        print(p.end)
        print(p.contents)


if __name__ == '__main__':
    main()
