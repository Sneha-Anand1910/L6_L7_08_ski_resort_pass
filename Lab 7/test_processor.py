from hypothesis import given, strategies as st
from processor import parse_season_pass_validity, compute_trail_gradient, calculate_lift_access_tier

@given(st.text() | st.none())
def test_parse_season_pass_validity_no_crash(s):
    #To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_compute_trail_gradient_safe(s):
    #To-Do:Using try and except complete this function.
    pass

@given(st.text() | st.none())
def test_calculate_lift_access_tier_safe(s):
    #To-Do:Using try and except complete this function.
    pass