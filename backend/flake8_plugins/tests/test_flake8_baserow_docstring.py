# Core Library
import ast
from typing import Set

from flake8_baserow.docstring import ERR_MSG
from flake8_baserow.docstring import Plugin as DocstringPlugin


def _results(s: str) -> Set[str]:
    tree = ast.parse(s)
    plugin = DocstringPlugin(tree, lines=s)
    return {f"{line}:{col} {msg}" for line, col, msg, _ in plugin.run()}


def test_trivial_case():
    assert _results("\n") == set()


def test_plugin_version():
    assert isinstance(DocstringPlugin.version, str)
    assert "." in DocstringPlugin.version


def test_plugin_name():
    assert isinstance(DocstringPlugin.name, str)


ERR_FUNC = """
def foo():
    '''
    foo
    '''
    print("hello")
"""

ERR_FUNC_2 = """
def foo():
    '''foo'''
    print("hello")
"""

ERR_FUNC_3 = """
def foo():
    '''foo'''
    # print hello
    print("hello")
"""


def test_missing_empty_line_after_docstring():
    for func, lineno in [(ERR_FUNC, 5), (ERR_FUNC_2, 3), (ERR_FUNC_3, 3)]:
        assert _results(func) == {f"{lineno}:4 {ERR_MSG}"}


OK_FUNC = """
def foo():
    '''
    foo

    '''

    print("hello")
"""

OK_FUNC_2 = """
def foo():
    '''foo'''

    print("hello")
"""

OK_FUNC_3 = """
def foo():
    '''
    foo
    '''
   
    # print hello
    print("hello")
"""


def test_noerrors_if_empty_line_after_docstring_is_present():
    for func in [OK_FUNC, OK_FUNC_2, OK_FUNC_3]:
        assert _results(func) == set()
