from FZBypass.core.bot_utils import (\n    convert_time,\n    get_gdriveid,\n    get_readable_size,\n    progress_bar,\n)


def test_convert_time_zero():
    assert convert_time(0) == "0ms"


def test_convert_time_seconds():
    assert convert_time(1.25) == "1s250ms"


def test_get_readable_size_zero():
    assert get_readable_size(0) == "0B"


def test_progress_bar_clamps_values():
    assert progress_bar(-10) == "[□□□□□□□□□□□□]"
    assert progress_bar(150) == "[■■■■■■■■■■■■]"


def test_get_gdriveid_from_folder_url():
    assert get_gdriveid("https://drive.google.com/drive/folders/AbC_123-xyz") == "AbC_123-xyz"


def test_get_gdriveid_from_query_url():
    assert get_gdriveid("https://drive.google.com/open?id=AbC_123-xyz") == "AbC_123-xyz"
