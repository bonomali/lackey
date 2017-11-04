import os

import lackey
import pytest


@pytest.fixture()
def kb():
    return lackey.Keyboard()


@pytest.fixture()
def mouse():
    return lackey.Mouse()


@pytest.fixture()
def screen():
    return lackey.Screen(0)


@pytest.fixture()
def test_loc():
    return lackey.Location(10, 11)


@pytest.fixture()
def pattern_path():
    return os.path.join("tests", "test_pattern.png")


@pytest.fixture()
def pattern(pattern_path):
    print(pattern_path)
    return lackey.Pattern(pattern_path)
