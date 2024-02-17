import dataclasses
import itertools
import typing

import pytest

import ruiner


def pairwise(iterable):
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class Syntax:
    opening: str = "<!--"
    close: str = "-->"
    optional: str = "(optional)"
    param: str = "(param)"
    ref: str = "(ref)"


class TestLists:
    class Valid:
        other: typing.List[str] = ["", " ", "la"]
        gap: typing.List[str] = ["", " ", "  "]
        value: typing.List[str] = ["", "l", "la", "\n"]

        ref: typing.List[str] = [f"{Syntax.opening}{Syntax.param}p{Syntax.close}"]

        one_line_params_number: typing.List[int] = [2, 3]

    class Invalid:
        gap: typing.List[str] = ["l", "la"]

        open_tag: typing.List[str] = [Syntax.close] + [Syntax.opening[:k] for k in range(len(Syntax.opening) - 1)]
        close_tag: typing.List[str] = [Syntax.opening] + [Syntax.close[:k] for k in range(len(Syntax.close) - 1)]

        name: typing.List[str] = ["1", "-", "1l"]


@dataclasses.dataclass(frozen=True)
class Line:
    expression: str
    name: str
    other_left: str = ""
    open_tag: str = Syntax.opening
    gap_left: str = " "
    flag: str = ""
    gap_right: str = " "
    close_tag: str = Syntax.close
    other_right: str = ""

    def __str__(self):
        return "".join(
            [
                self.other_left,
                self.open_tag,
                self.gap_left,
                self.flag,
                self.expression,
                self.name,
                self.gap_right,
                self.close_tag,
                self.other_right,
            ]
        )


@pytest.mark.parametrize(
    "value", TestLists.Valid.value + [list(e) for e in itertools.permutations(TestLists.Valid.value, 4)]
)
@pytest.mark.parametrize("other_left", TestLists.Valid.other + [Syntax.opening])
@pytest.mark.parametrize("gap_left", TestLists.Valid.gap)
@pytest.mark.parametrize("gap_right", TestLists.Valid.gap)
@pytest.mark.parametrize("other_right", TestLists.Valid.other + [Syntax.close])
def test_param_valid(
    value: typing.Union[str, typing.List[str]], other_left: str, gap_left: str, gap_right: str, other_right: str
):
    result = ruiner.Template(
        str(
            Line(
                expression=Syntax.param,
                name="p",
                other_left=other_left,
                gap_left=gap_left,
                gap_right=gap_right,
                other_right=other_right,
            )
        )
    ).rendered({"p": value})
    if isinstance(value, str):
        assert result == f"{other_left}{value}{other_right}"
    else:
        assert result == "\n".join([f"{other_left}{v}{other_right}" for v in value])


@pytest.mark.parametrize("value", TestLists.Valid.value[:1])
@pytest.mark.parametrize("open_tag", TestLists.Invalid.open_tag)
@pytest.mark.parametrize("other_left", TestLists.Valid.other[:1])
@pytest.mark.parametrize("gap_left", TestLists.Invalid.gap)
@pytest.mark.parametrize("name", TestLists.Invalid.name)
@pytest.mark.parametrize("gap_right", TestLists.Invalid.gap)
@pytest.mark.parametrize("other_right", TestLists.Valid.other[:1])
@pytest.mark.parametrize("close_tag", TestLists.Invalid.close_tag)
def test_param_invalid(
    value: str,
    open_tag: str,
    other_left: str,
    gap_left: str,
    name: str,
    gap_right: str,
    other_right: str,
    close_tag: str,
):
    line = str(
        Line(
            expression=Syntax.param,
            open_tag=open_tag,
            other_left=other_left,
            gap_left=gap_left,
            name=name,
            gap_right=gap_right,
            other_right=other_right,
            close_tag=close_tag,
        )
    )
    assert ruiner.Template(line).rendered({name: value}) == line


@pytest.mark.parametrize(
    "lines_args",
    pairwise(
        itertools.product(
            TestLists.Valid.value,  # name
            TestLists.Valid.other + [Syntax.opening],  # other_left
            TestLists.Valid.gap,  # gap_left
            TestLists.Valid.gap,  # gap_right
            TestLists.Valid.other + [Syntax.close],  # other_right
        )
    ),
)
def test_multiple_param_valid(lines_args: typing.List[str]):
    assert ruiner.Template(
        "\n".join(
            str(
                Line(
                    expression=Syntax.param,
                    name=f"p{i}",
                    other_left=a[1],
                    gap_left=a[2],
                    gap_right=a[3],
                    other_right=a[4],
                )
            )
            for i, a in enumerate(lines_args)
        )
    ).rendered({f"p{i}": a[0] for i, a in enumerate(lines_args)}) == "\n".join(
        f"{a[1]}{a[0]}{a[4]}" for a in lines_args
    )


@pytest.mark.parametrize("ref", TestLists.Valid.ref)
@pytest.mark.parametrize(
    "value", TestLists.Valid.value + [list(e) for e in itertools.permutations(TestLists.Valid.value, 4)]
)
@pytest.mark.parametrize("other_left", TestLists.Valid.other + [Syntax.opening])
@pytest.mark.parametrize("gap_left", TestLists.Valid.gap)
@pytest.mark.parametrize("gap_right", TestLists.Valid.gap)
@pytest.mark.parametrize("other_right", TestLists.Valid.other + [Syntax.close])
def test_ref_valid(
    ref: str,
    value: typing.Union[str, typing.List[str]],
    other_left: str,
    gap_left: str,
    gap_right: str,
    other_right: str,
):
    result = ruiner.Template(
        str(
            Line(
                expression=Syntax.ref,
                name="R",
                other_left=other_left,
                gap_left=gap_left,
                gap_right=gap_right,
                other_right=other_right,
            )
        )
    ).rendered({"R": {"p": value}}, {"R": ruiner.Template(ref)})
    if isinstance(value, str):
        assert result == other_left + value + other_right
    else:
        assert "\n".join(other_left + v + other_right for v in value)
