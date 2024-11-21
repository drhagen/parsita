import pytest

from parsita import ParserContext, Success, lit


def convert(value: str) -> str:
    return "global"


class GlobalGlobal(ParserContext):
    x = lit("x") > convert

    class Inner(ParserContext):
        x = lit("x") > convert


def test_global_class_global_function():
    assert GlobalGlobal.x.parse("x") == Success("global")
    assert GlobalGlobal.Inner.x.parse("x") == Success("global")


class GlobalLocal(ParserContext):
    def convert(value: str) -> str:
        return "local"

    x = lit("x") > convert

    class Inner(ParserContext):
        x = lit("x") > convert


def test_global_class_local_function():
    assert GlobalLocal.x.parse("x") == Success("local")
    assert GlobalLocal.Inner.x.parse("x") == Success("local")


class GlobalInner(ParserContext):
    def convert(value: str) -> str:
        return "local"

    x = lit("x") > convert

    class Inner(ParserContext):
        def convert(value: str):
            return "inner"

        x = lit("x") > convert


def test_global_class_inner_function():
    assert GlobalInner.x.parse("x") == Success("local")
    assert GlobalInner.Inner.x.parse("x") == Success("inner")


def test_local_class_global_function():
    class LocalGlobal(ParserContext):
        x = lit("x") > convert

        class Inner(ParserContext):
            x = lit("x") > convert

    assert LocalGlobal.x.parse("x") == Success("global")
    assert LocalGlobal.Inner.x.parse("x") == Success("global")


def test_local_class_local_function():
    class LocalLocal(ParserContext):
        def convert(value: str) -> str:
            return "local"

        x = lit("x") > convert

        class Inner(ParserContext):
            x = lit("x") > convert

    assert LocalLocal.x.parse("x") == Success("local")
    assert LocalLocal.Inner.x.parse("x") == Success("local")


def test_inner_class_inner_function():
    class LocalLocal(ParserContext):
        def convert(value: str) -> str:
            return "local"

        x = lit("x") > convert

        class Inner(ParserContext):
            def convert(value: str) -> str:
                return "nested"

            x = lit("x") > convert

    assert LocalLocal.x.parse("x") == Success("local")
    assert LocalLocal.Inner.x.parse("x") == Success("nested")


def test_nested_class_global_function():
    def nested() -> type[ParserContext]:
        class LocalLocal(ParserContext):
            x = lit("x") > convert

            class Inner(ParserContext):
                x = lit("x") > convert

        return LocalLocal

    returned_class = nested()
    assert returned_class.x.parse("x") == Success("global")
    assert returned_class.Inner.x.parse("x") == Success("global")


def factory():
    def convert(value: str) -> str:
        return "local"

    class LocalLocal(ParserContext):
        x = lit("x") > convert

        class Inner(ParserContext):
            x = lit("x") > convert

    return LocalLocal


def test_factory_class_local_function():
    def convert(value: str) -> str:
        return "caller"

    returned_class = factory()
    assert returned_class.x.parse("x") == Success("local")
    with pytest.xfail():
        assert returned_class.Inner.x.parse("x") == Success("local")


def test_nested_class_nonlocal_function():
    def convert(value: str) -> str:
        return "nonlocal"

    def nested() -> type[ParserContext]:
        class LocalLocal(ParserContext):
            x = lit("x") > convert

            class Inner(ParserContext):
                x = lit("x") > convert

        return LocalLocal

    returned_class = nested()
    assert returned_class.x.parse("x") == Success("nonlocal")
    with pytest.xfail():
        assert returned_class.Inner.x.parse("x") == Success("nonlocal")


def test_nested_class_local_function():
    def convert(value: str) -> str:
        return "nonlocal"

    def nested() -> type[ParserContext]:
        def convert(value: str):
            return "local"

        class LocalLocal(ParserContext):
            x = lit("x") > convert

            class Inner(ParserContext):
                x = lit("x") > convert

        return LocalLocal

    returned_class = nested()
    assert returned_class.x.parse("x") == Success("local")
    with pytest.xfail():
        assert returned_class.Inner.x.parse("x") == Success("local")
