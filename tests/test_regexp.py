from chartpress import _strip_identifiers_build_suffix
from chartpress import _get_identifier

def test__strip_identifiers_build_suffix():
    assert _strip_identifiers_build_suffix(identifier="0.1.2-005.asdf1234") == "0.1.2"
    assert _strip_identifiers_build_suffix(identifier="0.1.2-alpha.1.005.asdf1234") == "0.1.2-alpha.1"

def test__get_identifier():
    assert _get_identifier(tag="0.1.2",         n_commits="0", commit="asdf123",  long=True)  == "0.1.2-000.asdf123"
    assert _get_identifier(tag="0.1.2",         n_commits="0", commit="asdf123",  long=False) == "0.1.2"
    assert _get_identifier(tag="0.1.2",         n_commits="5", commit="asdf123",  long=False) == "0.1.2-005.asdf123"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=True)  == "0.1.2-alpha.1.000.asdf1234"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="0", commit="asdf1234", long=False) == "0.1.2-alpha.1"
    assert _get_identifier(tag="0.1.2-alpha.1", n_commits="5", commit="asdf1234", long=False) == "0.1.2-alpha.1.005.asdf1234"
