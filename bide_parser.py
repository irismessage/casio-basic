import re
from enum import Enum
from pathlib import Path


# todo: check accuracy of prog name re
PROG_CALL_RE = re.compile(r'Prog "([A-Z0-9~]+)"')


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


Parts = list[BidePart]
ProgramMap = dict[str, ProgramPart]


def parse_file(file: Path) -> Parts:
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


def filter_programs(parts: Parts) -> ProgramMap:
    return {p.name: p for p in parts if p.type == PartTypes.PROGRAM}


def minify(program: ProgramPart):
    lines = program.contents
    for i in range(len(lines) - 1, -1, -1):
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


def link_programs(programs: ProgramMap, entry_point_name: str) -> ProgramPart:
    entry_point = None
    for name, p in programs.items():
        if name == entry_point_name:
            entry_point = p
            break
        raise ValueError(f'Program with name "{entry_point_name}" is not present in {programs}.')

    while True:
        all_linked = True

        # todo: optimise with jumps
        for i in range(len(entry_point.contents) - 1, -1, -1):
            li = entry_point.contents[i]
            call = PROG_CALL_RE.match(li)
            if call is not None:
                all_linked = False
                call_name = call[1]
                call_prog = programs[call_name]
                # replace program call with full program contents
                entry_point.contents[i:i + 1] = call_prog.contents

        if all_linked:
            break

    return entry_point


def link_bide(bide_path: Path, out_path: Path, entry_point_name: str):
    parts = parse_file(bide_path)
    programs = filter_programs(parts)
    for p in programs.values():
        minify(p)
    linked = link_programs(programs, entry_point_name)
    linked_string = program_to_bide(linked)
    with open(out_path, 'w') as out_file:
        out_file.write(linked_string)


def main():
    file = Path('snake.bide')
    out = Path('snake_linked.bide')
    link_bide(file, out, '"SNAKE"')


if __name__ == '__main__':
    main()
