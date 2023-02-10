import re

from _pytest.fixtures import fixture
from changelog_legacy_converter import main

from changelog import purge, release

legacy_changelog = open("../changelog.md", "r")

"""
WARNING
These test will alter your file system. Don't run them if you have unsaved
changes!

You will also need to call this file from the root (/changelog) dir to make
the paths work!
"""


@fixture
def changelog():
    # Make sure everything is deleted first
    purge()

    # Generate the changelog json files
    main()

    # Make a release to generate the changelog.md
    release("Add", "./src")

    return open("./src/changelog.md", "r")


def get_unique_tokens_from_file(file):
    tokens = set()
    for line in file:
        words = re.split(" |_", line)

        words_sanitised = [
            "".join(e for e in word if e.isalnum()).lower() for word in words
        ]

        tokens = tokens.union(set(words_sanitised))
    return tokens


def test_token_match(changelog):
    tokens_to_ignore = {"unreleased"}

    tokens_legacy = get_unique_tokens_from_file(legacy_changelog).union(
        tokens_to_ignore
    )
    tokens_generated = get_unique_tokens_from_file(changelog).union(tokens_to_ignore)

    assert tokens_legacy == tokens_generated


# Note: commented out for now since we need some more sanitising to make this
# test work properly
# def test_lines_match():
#     # Load the generated changelog
#     generated_changelog = open("changelog.md", "r")
#
#     assert set(generated_changelog.readlines()) == set(legacy_changelog.readlines())
