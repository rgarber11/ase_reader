from __future__ import annotations

import dataclasses
import struct
from typing import BinaryIO, NamedTuple

from ase_reader.color import Color, ColorSpace, ColorType

GROUP_START = -16383
GROUP_END = -16382
COLOR = 1


@dataclasses.dataclass()
class Group:
    name: str
    groups: list[Group]
    colors: list[Color]

    def to_json(self: Group):
        return f"""{{
            "name": "{self.name}",
            "groups": [{",\n".join(in_group.to_json() for in_group in self.groups)}],
            "colors": [{",\n".join(color.to_json() for color in self.colors)}]
        }}"""


class ASE(NamedTuple):
    groups: list[Group]
    colors: list[Color]

    def to_json(self):
        return f"""{{
        "groups": [{",\n".join(group.to_json() for group in self.groups)}],
        "colors": [{",\n".join(color.to_json() for color in self.colors)}]
        }}"""


def readASE(fp: BinaryIO) -> ASE:
    groupStack: list[Group] = []
    groupStack.append(Group("root", [], []))
    _ = fp.seek(8)
    numBlocks: int
    (numBlocks,) = struct.unpack(">i", fp.read(4))
    for block in range(numBlocks):
        block_type: int
        block_length: int
        block_type, block_length = struct.unpack(">hi", fp.read(6))
        offset = fp.tell()
        if block_type == GROUP_START:
            name_length: int
            name_bytes: bytes
            (name_length,) = struct.unpack(">H", fp.read(2))
            (name_bytes,) = struct.unpack(
                f">{name_length * 2}s", fp.read(name_length * 2)
            )
            name_str = name_bytes.decode("utf-16be").rstrip("\x00")
            groupStack[-1].groups.append(Group(name_str, [], []))
            groupStack.append(groupStack[-1].groups[-1])
        elif block_type == GROUP_END:
            _ = groupStack.pop()
        elif block_type == COLOR:
            color_space_raw: bytes
            color_vals: tuple[float, ...]
            color_type: int
            (name_length,) = struct.unpack(">H", fp.read(2))
            (name_bytes,) = struct.unpack(
                f">{name_length * 2}s", fp.read(name_length * 2)
            )
            name_str = name_bytes.decode("utf-16be").rstrip("\x00")
            (color_space_raw,) = struct.unpack(">4s", fp.read(4))
            color_space_str: str = color_space_raw.decode("ascii").rstrip()
            if color_space_str == "RGB":
                color_vals = struct.unpack(">3f", fp.read(12))
                (color_type,) = struct.unpack(">h", fp.read(2))
                groupStack[-1].colors.append(
                    Color(
                        name_str,
                        ColorSpace.RGB,
                        color_vals,
                        ColorType(color_type),
                    )
                )
            elif color_space_str == "CMYK":
                color_vals = struct.unpack(">4f", fp.read(16))
                (color_type,) = struct.unpack(">h", fp.read(2))
                groupStack[-1].colors.append(
                    Color(
                        name_str,
                        ColorSpace.CMYK,
                        color_vals,
                        ColorType(color_type),
                    )
                )
            elif color_space_str == "LAB":
                color_vals = struct.unpack(">3f", fp.read(12))
                (color_type,) = struct.unpack(">h", fp.read(2))
                groupStack[-1].colors.append(
                    Color(
                        name_str,
                        ColorSpace.LAB,
                        color_vals,
                        ColorType(color_type),
                    )
                )
            elif color_space_str == "Gray":
                color_vals = struct.unpack(">fh", fp.read(4))
                (color_type,) = struct.unpack(">h", fp.read(2))
                groupStack[-1].colors.append(
                    Color(
                        name_str,
                        ColorSpace.GRAY,
                        color_vals,
                        ColorType(color_type),
                    )
                )

            else:
                raise Exception("Invalid Color Space")

        else:
            raise Exception("Invalid Block Type within ASE")
        _ = fp.seek(block_length - (fp.tell() - offset), 1)
    return ASE(groupStack[0].groups, groupStack[0].colors)


def readASEFile(filename: str) -> ASE:
    with open(filename, "rb") as file:
        return readASE(file)


def main():
    colors = readASEFile("SAP RGB.ase")
    print(colors.to_json())


if __name__ == "__main__":
    main()
