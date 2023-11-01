import ruiner
import pytest
import itertools
import dataclasses


class Syntax:
    open: str = "<!--"
    close: str = "-->"
    optional: str = "(optional)"
    param: str = "(param)"
    ref: str = "(ref)"


class TestLists:
    class Valid:
        other: list[str] = ["", " ", "la"]
        gap: list[str] = ["", " ", "  "]
        value: list[str] = ["", "l", "la", "\n"]

        ref: list[str] = [f"{Syntax.open}{Syntax.param}p{Syntax.close}"]

        one_line_params_number: list[int] = [2, 3]

    class Invalid:
        gap: list[str] = ["l", "la"]

        open_tag: list[str] = [Syntax.close] + [
            Syntax.open[:k] for k in range(len(Syntax.open) - 1)
        ]
        close_tag: list[str] = [Syntax.open] + [
            Syntax.close[:k] for k in range(len(Syntax.close) - 1)
        ]

        name: list[str] = ["1", "-", "1l"]


@dataclasses.dataclass(frozen=True, kw_only=True)
class Line:
    type: str
    name: str
    other_left: str = ""
    open_tag: str = Syntax.open
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
                self.type,
                self.name,
                self.gap_right,
                self.close_tag,
                self.other_right,
            ]
        )


@pytest.mark.parametrize(
    "value",
    TestLists.Valid.value
    + [list(e) for e in itertools.permutations(TestLists.Valid.value, 4)],
)
@pytest.mark.parametrize("other_left", TestLists.Valid.other + [Syntax.open])
@pytest.mark.parametrize("gap_left", TestLists.Valid.gap)
@pytest.mark.parametrize("gap_right", TestLists.Valid.gap)
@pytest.mark.parametrize("other_right", TestLists.Valid.other + [Syntax.close])
def test_param_valid(
    value: str | list[str],
    other_left: str,
    gap_left: str,
    gap_right: str,
    other_right: str,
):
    # print([list(t) for t in itertools.permutations(TestLists.Valid.value, 4)])
    # exit()
    # assert False
    result = ruiner.Template(
        str(
            Line(
                type=Syntax.param,
                name="p",
                other_left=other_left,
                gap_left=gap_left,
                gap_right=gap_right,
                other_right=other_right,
            )
        )
    ).rendered({"p": value}, {})
    match value:
        case str():
            assert result == f"{other_left}{value}{other_right}"
        case _:
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
    assert (
        ruiner.Template(
            line := str(
                Line(
                    type=Syntax.param,
                    open_tag=open_tag,
                    other_left=other_left,
                    gap_left=gap_left,
                    name=name,
                    gap_right=gap_right,
                    other_right=other_right,
                    close_tag=close_tag,
                )
            )
        ).rendered({name: value})
        == f"{line}"
    )


@pytest.mark.parametrize(
    "lines_args",
    itertools.pairwise(
        itertools.product(
            TestLists.Valid.value,  # name
            TestLists.Valid.other + [Syntax.open],  # other_left
            TestLists.Valid.gap,  # gap_left
            TestLists.Valid.gap,  # gap_right
            TestLists.Valid.other + [Syntax.close],  # other_right
        )
    ),
)
def test_multiple_param_valid(lines_args: list[str]):
    assert ruiner.Template(
        "\n".join(
            str(
                Line(
                    type=Syntax.param,
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
    "value",
    TestLists.Valid.value
    + [list(e) for e in itertools.permutations(TestLists.Valid.value, 4)],
)
@pytest.mark.parametrize("other_left", TestLists.Valid.other + [Syntax.open])
@pytest.mark.parametrize("gap_left", TestLists.Valid.gap)
@pytest.mark.parametrize("gap_right", TestLists.Valid.gap)
@pytest.mark.parametrize("other_right", TestLists.Valid.other + [Syntax.close])
def test_ref_valid(
    ref: str,
    value: str | list[str],
    other_left: str,
    gap_left: str,
    gap_right: str,
    other_right: str,
):
    result = ruiner.Template(
        str(
            Line(
                type=Syntax.ref,
                name="R",
                other_left=other_left,
                gap_left=gap_left,
                gap_right=gap_right,
                other_right=other_right,
            )
        )
    ).rendered({"R": {"p": value}}, {"R": ruiner.Template(ref)})
    match value:
        case str():
            assert result == other_left + value + other_right
        case _:
            assert "\n".join(other_left + v + other_right for v in value)
