from src.trash import generate_trash_string


def test_generate_trash_string():
    ans = generate_trash_string(2)
    assert len(ans) == 2


def test_trash_string_unique():
    assert generate_trash_string(5) != generate_trash_string(5)
