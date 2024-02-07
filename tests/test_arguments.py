import importlib
import os
import pytest
import re

SCRIPT_NAME = 'email-output'

script_module = importlib.import_module(SCRIPT_NAME)

@pytest.fixture
def script_main_function():
    return script_module.main

@pytest.fixture
def help_output_regex():
    return r'^usage: %s\.py ' % SCRIPT_NAME

@pytest.fixture
def version_output_regex():
    return r'^%s\.py [0-9]\.[0-9]$' % SCRIPT_NAME

def test_main_without_args_fail_and_output_help(script_main_function, capsys, help_output_regex):
    with pytest.raises(SystemExit) as e:
        script_main_function()
    assert e.type == SystemExit
    assert e.value.code == 2
    captured = capsys.readouterr()
    assert re.match(help_output_regex, captured.err)

def test_main_minus_h_output_help(script_main_function, capsys, help_output_regex):
    with pytest.raises(SystemExit) as e:
        script_main_function('-h')
    assert e.type == SystemExit
    assert e.value.code == os.EX_OK
    captured = capsys.readouterr()
    assert re.match(help_output_regex, captured.out)

def test_main_minus_minus_help_output_help(script_main_function, capsys, help_output_regex):
    with pytest.raises(SystemExit) as e:
        script_main_function('--help')
    assert e.type == SystemExit
    assert e.value.code == os.EX_OK
    captured = capsys.readouterr()
    assert re.match(help_output_regex, captured.out)

def test_main_minus_capital_v_output_version(script_main_function, capsys, version_output_regex):
    with pytest.raises(SystemExit) as e:
        script_main_function('-V')
    assert e.type == SystemExit
    assert e.value.code == os.EX_OK
    captured = capsys.readouterr()
    assert re.match(version_output_regex, captured.out)

def test_main_minus_minus_version_output_version(script_main_function, capsys, version_output_regex):
    with pytest.raises(SystemExit) as e:
        script_main_function('--version')
    assert e.type == SystemExit
    assert e.value.code == os.EX_OK
    captured = capsys.readouterr()
    assert re.match(version_output_regex, captured.out)
