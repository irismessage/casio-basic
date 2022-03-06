import re
import string
from argparse import ArgumentParser
from enum import Enum
from pathlib import Path


# todo: check accuracy of prog name re
PROG_CALL_RE = re.compile('Prog "([A-Z0-9~]+)"')
LBL_RE = re.compile('^Lbl ([A-Z0-9])$')
LBL_F = 'Lbl {}'
GOTO_F = 'Goto {}'


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


def label_reassignment(programs: ProgramMap):
    available = [*string.ascii_uppercase, *string.digits]

    for p in programs.values():
        contents = '\n'.join(p.contents)
        all_lbls = LBL_RE.findall(contents)
        for lbl_match in all_lbls:
            try:
                new_lbl = available.pop()
            except IndexError as e:
                raise IndexError('Out of labels') from e

            old_lbl = lbl_match[1]
            contents.replace(LBL_F.format(old_lbl), LBL_F.format(new_lbl))
            contents.replace(GOTO_F.format(old_lbl), GOTO_F.format(new_lbl))

        p.contents = contents.splitlines()


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


def get_parser() -> ArgumentParser:
    parser = ArgumentParser()

    parser.add_argument('-i', '--input', type=Path, default='snake.bide')
    parser.add_argument('-o', '--output', type=Path, default='snake_linked.bide')
    parser.add_argument('-e', '--entry', default='"SNAKE"', help='Name of the entry point program to link')

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    link_bide(args.input, args.output, args.entry)


if __name__ == '__main__':
    main()
