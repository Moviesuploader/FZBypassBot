from FZBypass.core.bot_utils import convert_time, get_readable_size, progress_bar


def test_convert_time_zero():
    assert convert_time(0) == "0ms"


def test_convert_time_seconds():
    assert convert_time(1.25) == "1s250ms"


def test_get_readable_size_zero():
    assert get_readable_size(0) == "0B"


def test_progress_bar_clamps_values():
    assert progress_bar(-10) == "[□□□□□□□□□□□□]"
    assert progress_bar(150) == "[■■■■■■■■■■■■]"
