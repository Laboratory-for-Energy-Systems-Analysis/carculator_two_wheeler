import json
from pathlib import Path

import pytest

import carculator_two_wheeler.two_wheelers_input_parameters as cip

DEFAULT = Path(__file__, "..").resolve() / "fixtures" / "default_test.json"
EXTRA = Path(__file__, "..").resolve() / "fixtures" / "extra_test.json"


def test_retrieve_list_powertrains():
    assert isinstance(cip.TwoWheelerInputParameters().powertrains, list)
    assert len(cip.TwoWheelerInputParameters().powertrains) > 5


def test_can_pass_directly():
    d, e = json.load(open(DEFAULT)), set(json.load(open(EXTRA)))
    e.remove("foobazzle")
    assert len(cip.TwoWheelerInputParameters(d, e).powertrains) == 5
    assert len(cip.TwoWheelerInputParameters(d, e).parameters) == 12


def test_alternate_filepath():
    assert len(cip.TwoWheelerInputParameters(DEFAULT, EXTRA).powertrains) == 5
    assert len(cip.TwoWheelerInputParameters(DEFAULT, EXTRA).parameters) == 13
