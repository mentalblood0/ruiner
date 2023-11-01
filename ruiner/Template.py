import re
import typing
import functools
import contextlib
import dataclasses

from .Regexp import Regexp


@dataclasses.dataclass(frozen=True, kw_only=False)
class Pattern:
    value: str

    expression = Regexp(re.compile(".*"))

    @functools.cached_property
    def match(self):
        if not (result := self.expression.match(self.value)):
            raise ValueError(
                f'Expression "{self.expression}"' f'does not match value "{self.value}"'
            )
        return result

    def __post_init__(self):
        self.match

    @functools.cached_property
    def groups(self):
        return self.match.groupdict()

    @classmethod
    @functools.lru_cache
    def extracted(cls, source: "Pattern"):
        return [
            cls(source.value[m.start() : m.end()])
            for m in cls.expression.find(source.value)
        ]

    @classmethod
    @functools.lru_cache
    def highlighted(cls, source: "Pattern"):
        result: list[Other | cls] = []
        last_end = 0
        for m in cls.expression.find(source.value):
            result += [
                Other(source.value[last_end : m.start()]),
                cls(source.value[m.start() : m.end()]),
            ]
            last_end = m.end()
        result.append(Other(source.value[last_end:]))
        return [r for r in result if r.value]

    def __getitem__(self, name: str):
        return self.groups[name]

    def __contains__(self, name: str):
        return name in self.groups and self.groups[name] is not None


class Name(Pattern):
    expression = Regexp(re.compile("\\w+"))


class Spaces(Pattern):
    expression = Regexp(re.compile(" *"))


class Open(Pattern):
    expression = Regexp(re.compile("<!--"))


class Close(Pattern):
    expression = Regexp(re.compile("-->"))


class Delimiter(Pattern):
    expression = Regexp(re.compile("\n"))


class Other(Pattern):
    @property
    def rendered(self):
        return self.value


class Operator(Pattern):
    expression = Regexp(re.compile(f"\\({Name.expression}\\)"))


class Optional(Operator):
    expression = Regexp(re.compile(r"\(optional\)"))


class Expression(Pattern):
    class Type(Operator):
        class Parameter(Operator):
            expression = Regexp(re.compile(r"\(param\)"))

        class Reference(Operator):
            expression = Regexp(re.compile(r"\(ref\)"))

    expression = Regexp.sequence(
        Open.expression,
        Spaces.expression,
        Optional.expression("optional").optional,
        Type.expression,
        Name.expression("name"),
        Spaces.expression,
        Close.expression,
    )

    @functools.cached_property
    def name(self):
        return Name(self["name"])

    @property
    def optional(self):
        return "optional" in self

    @functools.cached_property
    def specified(self):
        with contextlib.suppress(ValueError):
            return Parameter(self.value)
        return Reference(self.value)


class Parameter(Expression):
    expression = Regexp.sequence(
        Open.expression,
        Spaces.expression,
        Optional.expression("optional").optional,
        Expression.Type.Parameter.expression,
        Name.expression("name"),
        Spaces.expression,
        Close.expression,
    )

    def _rendered(self, parameters: str | list[str] | list["Template.Parameters"]):
        match parameters:
            case list():
                return parameters
            case str():
                return [parameters]

    def rendered(self, parameters: "Template.Parameters", _: dict[str, "Template"]):
        try:
            if not isinstance(p := parameters[self.name.value], str | list):
                raise TypeError
            return self._rendered(p)
        except KeyError:
            if not self.optional:
                return [""]
            return list[str]()


class Reference(Expression):
    expression = Regexp.sequence(
        Open.expression,
        Spaces.expression,
        Optional.expression("optional").optional,
        Expression.Type.Reference.expression,
        Name.expression("name"),
        Spaces.expression,
        Close.expression,
    )

    def inner(self, parameters: "Template.Parameters"):
        if self.name.value in parameters:
            return parameters[self.name.value]
        else:
            return Template.Parameters({})

    def _rendered_optional(
        self, parameters: "Template.Parameters", templates: dict[str, "Template"]
    ):
        if self.name.value not in parameters:
            return [""]
        elif self.name.value not in templates:
            raise KeyError

    def _rendered(
        self,
        parameters: "Template.Parameters",
        templates: dict[str, "Template"],
        left: str = "",
        right: str = "",
    ):
        match (inner := self.inner(parameters)):
            case str():
                raise TypeError
            case list():
                result: list[str] = []
                for p in inner:
                    if isinstance(p, str):
                        raise TypeError
                    result.append(
                        templates[self.name.value].rendered(p, templates, left, right)
                    )
                return result
            case _:
                return [
                    templates[self.name.value].rendered(inner, templates, left, right)
                ]

    def rendered(
        self,
        parameters: "Template.Parameters",
        templates: dict[str, "Template"],
        left: str = "",
        right: str = "",
    ) -> list[str]:
        result = self._rendered_optional(parameters, templates)
        if self.optional and result is not None:
            return result
        return self._rendered(parameters, templates, left, right)


class Line(Pattern):
    class OneReference(Pattern):
        expression = Regexp.sequence(
            Other.expression.optional("left"),
            Reference.expression("reference"),
            Other.expression.optional("right"),
        )

        @functools.cached_property
        def left(self):
            return Other(self["left"]).rendered

        @functools.cached_property
        def reference(self):
            return Reference(self["reference"])

        @functools.cached_property
        def right(self):
            return Other(self["right"]).rendered

        def rendered(
            self,
            parameters: "Template.Parameters",
            templates: dict[str, "Template"],
            left: str = "",
            right: str = "",
        ):
            return str(Delimiter.expression).join(
                self.reference.rendered(
                    parameters, templates, left + self.left, self.right + right
                )
            )

    @functools.cached_property
    def specified(self):
        if len(Reference.extracted(self)) == 1:
            return Line.OneReference(self.value)
        else:
            return self

    def _rendered(self, inner: tuple[str]):
        current = iter(inner)
        return "".join(
            e.value if isinstance(e, Other) else next(current)
            for e in Expression.highlighted(self)
        )

    def rendered(
        self,
        parameters: "Template.Parameters",
        templates: dict[str, "Template"],
        left: str = "",
        right: str = "",
    ):
        if not len(extracted := Expression.extracted(self)):
            return left + self.value + right
        else:
            return str(Delimiter.expression).join(
                [
                    left + self._rendered(inner) + right
                    for inner in zip(
                        *[
                            p.specified.rendered(parameters, templates)
                            for p in extracted
                        ]
                    )
                ]
            )


class Template(Pattern):
    Parameters = dict[
        str, typing.Union[str, list[str], "Parameters", list["Parameters"]]
    ]

    expression = Regexp(re.compile("(?:.*\n)*(?:.*)?"))

    @functools.cached_property
    def lines(self):
        return [
            Line(line).specified for line in self.value.split(str(Delimiter.expression))
        ]

    def rendered(
        self,
        parameters: "Template.Parameters",
        templates: dict[str, "Template"] | None = None,
        left: str = "",
        right: str = "",
    ):
        templates = templates or {}
        return str(Delimiter.expression).join(
            [line.rendered(parameters, templates, left, right) for line in self.lines]
        )
