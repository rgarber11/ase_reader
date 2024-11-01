from __future__ import annotations

import dataclasses
from enum import Enum, auto
from typing import cast


class ColorSpace(Enum):
    CMYK = auto()
    RGB = auto()
    LAB = auto()
    GRAY = auto()


class ColorType(Enum):
    GLOBAL = 0
    SPOT = 1
    NORMAL = 2


@dataclasses.dataclass()
class Color:
    name: str
    space: ColorSpace
    vals: tuple[float, ...]
    color_type: ColorType

    def to_json(self):
        return f"""{{
            "name": "{self.name}",
            "space": "{self.space.name}",
            "vals": {list(self.vals)},
            "color_type": "{self.color_type.name}"
        }}"""

    @staticmethod
    def _f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + (16 / 116)

    @staticmethod
    def _fminus1(t: float) -> float:
        return (
            t**3
            if t > 0.2068930344229638340625143655415740795433521270751953125
            else (t - (16 / 116)) / 7.787
        )

    @staticmethod
    def cmyk_to_rgb(
        vals: tuple[float, float, float, float]
    ) -> tuple[float, float, float]:
        return (
            1 - (1 - vals[3]) * vals[0] - vals[3],
            1 - (1 - vals[3]) * vals[1] - vals[3],
            1 - (1 - vals[3]) * vals[2] - vals[3],
        )

    @staticmethod
    def lab_to_rgb(vals: tuple[float, float, float]) -> tuple[float, float, float]:
        y = (
            ((vals[0] + 16) / 116) ** 3
            if vals[0] > 7.999591993063805972496993490494787693023681640625
            else vals[0] / 903.3
        )
        fy = Color._f(y)
        x = Color._fminus1(vals[1] / 500 + fy) * 0.950456
        z = -Color._fminus1(vals[2] / 200 - fy) * 1.088754
        r = (
            3.2404813432005266093938189442269504070281982421875 * x
            + -1.5371515162713185187470799064612947404384613037109375 * y
            + -0.498536326168887822252173691595089621841907501220703125 * z
        )
        g = (
            -0.96925494999656824912648289682692848145961761474609375 * x
            + 1.8759900014898907016913653933443129062652587890625 * y
            + 0.041555926558292842487585261324056773446500301361083984375 * z
        )
        b = (
            3.2404813432005266093938189442269504070281982421875 * x
            + 3.2404813432005266093938189442269504070281982421875 * y
            + 3.2404813432005266093938189442269504070281982421875 * z
        )
        return (r, g, b)

    @staticmethod
    def grayscale_to_rgb(val: float) -> tuple[float, float, float]:
        return (val, val, val)

    @staticmethod
    def rgb_to_cmyk(
        vals: tuple[float, float, float]
    ) -> tuple[float, float, float, float]:
        if vals[0] == 0 and vals[1] == 0 and vals[2] == 0:
            return (0, 0, 0, 1)
        black = min(1 - val for val in vals)
        return (
            ((1 - vals[0] - black) / (1 - black)),
            ((1 - vals[1] - black) / (1 - black)),
            ((1 - vals[2] - black) / (1 - black)),
            black,
        )

    @staticmethod
    def rgb_to_lab(vals: tuple[float, float, float]) -> tuple[float, float, float]:
        x = (0.412453 * vals[0] + 0.357580 * vals[1] + 0.180423 * vals[2]) / 0.950456
        y = 0.212671 * vals[0] + 0.715160 * vals[1] + 0.072169 * vals[2]
        z = (0.019334 * vals[0] + 0.119193 * vals[1] + 0.950227 * vals[2]) / 1.088754

        l: float = 116 * (y ** (1 / 3)) - 16 if y > 0.008856 else 903.3 * y
        a = 500 * (Color._f(x) - Color._f(y))
        b = 200 * (Color._f(y) - Color._f(z))
        return (l, a, b)

    @staticmethod
    def rgb_to_grayscale(vals: tuple[float, float, float]) -> float:
        return 0.299 * vals[0] + 0.587 * vals[1] + 0.114 * vals[2]

    def to_cmyk(self: Color) -> Color:
        if self.space is ColorSpace.CMYK:
            return dataclasses.replace(self)
        elif self.space is ColorSpace.RGB:
            return dataclasses.replace(
                self,
                space=ColorSpace.CMYK,
                vals=Color.rgb_to_cmyk(cast(tuple[float, float, float], self.vals)),
            )
        elif self.space is ColorSpace.GRAY:
            return dataclasses.replace(
                self,
                space=ColorSpace.CMYK,
                vals=Color.rgb_to_cmyk((self.vals[0], self.vals[0], self.vals[0])),
            )
        else:
            return dataclasses.replace(
                self,
                space=ColorSpace.CMYK,
                vals=Color.rgb_to_cmyk(
                    Color.lab_to_rgb(cast(tuple[float, float, float], self.vals))
                ),
            )

    def to_rgb(self: Color) -> Color:
        if self.space is ColorSpace.RGB:
            return dataclasses.replace(self)
        elif self.space is ColorSpace.CMYK:
            return dataclasses.replace(
                self,
                space=ColorSpace.RGB,
                vals=Color.cmyk_to_rgb(
                    cast(tuple[float, float, float, float], self.vals)
                ),
            )
        elif self.space is ColorSpace.GRAY:
            return dataclasses.replace(
                self,
                space=ColorSpace.RGB,
                vals=(self.vals[0], self.vals[0], self.vals[0]),
            )
        else:
            return dataclasses.replace(
                self,
                space=ColorSpace.RGB,
                vals=Color.lab_to_rgb(cast(tuple[float, float, float], self.vals)),
            )

    def to_lab(self: Color) -> Color:
        if self.space is ColorSpace.LAB:
            return dataclasses.replace(self)
        elif self.space is ColorSpace.CMYK:
            return dataclasses.replace(
                self,
                space=ColorSpace.LAB,
                vals=Color.rgb_to_lab(
                    Color.cmyk_to_rgb(
                        cast(tuple[float, float, float, float], self.vals)
                    )
                ),
            )
        elif self.space is ColorSpace.GRAY:
            return dataclasses.replace(
                self,
                space=ColorSpace.LAB,
                vals=Color.rgb_to_lab((self.vals[0], self.vals[0], self.vals[0])),
            )
        else:
            return dataclasses.replace(
                self,
                space=ColorSpace.LAB,
                vals=Color.rgb_to_lab(cast(tuple[float, float, float], self.vals)),
            )

    def to_grayscale(self) -> Color:
        if self.space is ColorSpace.GRAY:
            return dataclasses.replace(self)
        elif self.space is ColorSpace.CMYK:
            return dataclasses.replace(
                self,
                space=ColorSpace.GRAY,
                vals=(
                    Color.rgb_to_grayscale(
                        Color.cmyk_to_rgb(
                            cast(tuple[float, float, float, float], self.vals)
                        )
                    ),
                ),
            )
        elif self.space is ColorSpace.RGB:
            return dataclasses.replace(
                self,
                space=ColorSpace.GRAY,
                vals=(
                    Color.rgb_to_grayscale(cast(tuple[float, float, float], self.vals)),
                ),
            )
        else:
            return dataclasses.replace(
                self,
                space=ColorSpace.GRAY,
                vals=(
                    Color.rgb_to_grayscale(
                        Color.lab_to_rgb(cast(tuple[float, float, float], self.vals))
                    ),
                ),
            )

    def get_8_bit_vals(self) -> tuple[int, ...]:
        if self.space is not ColorSpace.LAB:
            return tuple(int(val * 255) for val in self.vals)
        return (
            int(self.vals[0] * (255 / 100)),
            int(self.vals[1] + 128),
            int(self.vals[2] + 128),
        )
