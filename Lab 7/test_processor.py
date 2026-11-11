from hypothesis import given, strategies as st
from processor import (
    parse_season_pass_validity,
    compute_trail_gradient,
    calculate_lift_access_tier
)


@given(st.text() | st.none())
def test_parse_season_pass_validity_no_crash(s):
    try:
        parse_season_pass_validity(s)
    except Exception as e:
        assert False, f"parse_season_pass_validity crashed with input {s!r}: {e}"


@given(st.text() | st.none())
def test_compute_trail_gradient_safe(s):
    try:
        compute_trail_gradient(s)
    except Exception as e:
        assert False, f"compute_trail_gradient crashed with input {s!r}: {e}"


@given(st.text() | st.none())
def test_calculate_lift_access_tier_safe(s):
    try:
        calculate_lift_access_tier(s)
    except Exception as e:
        assert False, f"calculate_lift_access_tier crashed with input {s!r}: {e}"