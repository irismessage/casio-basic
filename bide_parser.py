from enum import Enum
from pathlib import Path


class PartTypes(Enum):
    BASE = 0
    PROGRAM = 1
    CAPTURE = 2
    PICTURES = 3


class BidePart:
    type = PartTypes.BASE

    def __init__(
            self, file: Path, name: str, start: int, end: int, contents: list[str]
    ):
        self.file = file
        self.name = name
        self.start = start
        self.end = end
        self.contents = self.parse_contents(contents)

    @staticmethod
    def parse_contents(contents: list[str]):
        return contents


class ProgramPart(BidePart):
    type = PartTypes.PROGRAM

    @staticmethod
    def parse_contents(contents: list[str]):
        # remove password line
        del contents[0]
        return contents


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
            # remove newline
            line = line[:-1]

            if not name:
                name = line.removeprefix('#Program name: ')
                start = lineno
            elif line == '#End of part':
                p = ProgramPart(file, name, start, lineno, contents_lines)
                parts.append(p)

                name = ''
                contents_lines = []
            else:
                contents_lines.append(line)

            lineno += 1

    return parts


def filter_programs(parts: list[BidePart]) -> dict[str, ProgramPart]:
    return {p.name: p for p in parts if p.type == PartTypes.PROGRAM}


def minify(program: ProgramPart):
    lines = program.contents
    for i in range(len(lines) - 1, 0, -1):
        li = lines[i]
        if (not li) or li.startswith("'"):
            del lines[i]


def program_to_bide(program: ProgramPart) -> str:
    bide_lines = [
        f'#Program name: {program.name}',
        '#Password: <no password>',
        *program.contents,
        '#End of part',
    ]
    bide = '\n'.join(bide_lines)
    return bide


def main():
    file = Path('snake.bide')
    parts = parse_file(file)
    programs = filter_programs(parts)
    for p in programs.values():
        minify(p)
        print(p)
        print(p.contents)


if __name__ == '__main__':
    main()
