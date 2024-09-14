import pytest

from .text_analyzer import word_stats


def test_word_stats_normal():
    result = word_stats('this is the string, for test.')
    assert result == {'word_count': 6, 'char_count': 24, 'avg_word_length': 4.0}


def test_word_stats_empty():
    assert word_stats('') == {'word_count': 0, 'char_count': 0, 'avg_word_length': 0.0}


def test_word_stats_spaces():
    assert word_stats('   ') == {'word_count': 0, 'char_count': 0, 'avg_word_length': 0.0}


def test_word_stats_single_word():
    result = word_stats('Python')
    assert result == {'word_count': 1, 'char_count': 6, 'avg_word_length': 6.0}


@pytest.mark.parametrize("input_string, expected", [
    ("a b c d", {'word_count': 4, 'char_count': 4, 'avg_word_length': 1.0}),
    ("Hello, World!", {'word_count': 2, 'char_count': 12, 'avg_word_length': 6.0}),
])
def test_word_stats_parametrized(input_string, expected):
    print("\ninput_string:", input_string)
    print("\nexpected: ", expected)
    assert word_stats(input_string) == expected
