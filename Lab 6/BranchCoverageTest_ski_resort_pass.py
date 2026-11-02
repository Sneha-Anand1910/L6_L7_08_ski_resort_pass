"""Independent branch suite including boundaries and control-flow interactions."""
import pytest
from ski_resort_pass import process_resort_bookings, check_chairlift_anemometer


def booking(duration="full_day", skiers=None, **options):
    return dict(is_active=True, duration=duration,
                skiers=[] if skiers is None else skiers, **options)


@pytest.mark.parametrize("groups,fee", [(None, 0), ([], -1), (None, -1)])
def test_validation_rejects(groups, fee):
    with pytest.raises(ValueError, match="^Invalid groups list or facility fee$"):
        process_resort_bookings(groups, fee)


@pytest.mark.parametrize("groups", [[], [{}], [{"is_active": False}], [booking()]])
def test_empty_and_skipped_loops(groups):
    assert process_resort_bookings(groups, 0) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


@pytest.mark.parametrize("duration", ["season", "full_day", "half_day"])
def test_duration_age_and_rental_branches(duration):
    # Child, lower/upper adult boundaries, senior, then override taking precedence.
    skiers = [{"age": 11}, {"age": 12}, {"age": 64},
              {"age": 65, "gear_rental": True},
              {"age": 11, "blackout_override": True}, {"age": 30}]
    # Non-half-day coefficient: .6 + 1 + 1 + .7 + .5 + 1 = 4.8.
    # Half-day override clears prior revenue and breaks before the final skier.
    expected = {"season": 1475.0, "full_day": 419.0, "half_day": 0.0}[duration]
    status = "ZERO_SALES" if duration == "half_day" else "COMPLETED"
    assert process_resort_bookings([booking(duration, skiers)], 0) == {
        "total_revenue": expected, "status": status}


@pytest.mark.parametrize("count,status", [(4, "COMPLETED"), (5, "AUDIT_REVIEW")])
def test_invalid_duration_counts_once_per_group(count, status):
    groups = [booking("invalid", [{"age": 0}] * 10, includes_lodge_locker=True) for _ in range(count)]
    groups += [booking(skiers=[{"age": 30}])]
    assert process_resort_bookings(groups, 15) == {"total_revenue": 80.0, "status": status}


@pytest.mark.parametrize("count,status", [(4, "ZERO_SALES"), (5, "AUDIT_REVIEW")])
def test_invalid_age_audit_precedes_zero_sales(count, status):
    skiers = [{"age": 0, "gear_rental": True, "blackout_override": True}, {"age": -1}, {}]
    skiers += [{"age": 0}] * (count - 3)
    assert process_resort_bookings([booking(skiers=skiers)], 0) == {"total_revenue": 0.0, "status": status}


def test_age_continue_and_group_continuation_after_break():
    groups = [booking("half_day", [{"age": 30, "gear_rental": True},
                                   {"age": 65, "blackout_override": True, "gear_rental": True},
                                   {"age": 30}], includes_lodge_locker=True),
              booking(skiers=[{"age": -1}, {"age": 30}])]
    assert process_resort_bookings(groups, 15.126) == {"total_revenue": 95.13, "status": "COMPLETED"}


def test_empty_group_still_charges_locker():
    assert process_resort_bookings([{"is_active": True, "includes_lodge_locker": True}], 12) == {
        "total_revenue": 12.0, "status": "COMPLETED"}


def test_blackout_rejections_with_positive_revenue_and_rental():
    skiers = [{"age": 65, "blackout_override": True, "gear_rental": True}] * 5
    assert process_resort_bookings([booking(skiers=skiers)], 0) == {
        "total_revenue": 375.0, "status": "AUDIT_REVIEW"}


@pytest.mark.parametrize("streams,expected", [
    ([], "NO_DATA"), ([[]], "SAFE_OPERATION"),
    ([[45, 0, 44]], "SAFE_OPERATION"), ([[45.001]], "SAFE_OPERATION"),
    ([[46, 45, 46]], "SAFE_OPERATION"), ([[46], [], [46]], "SAFE_OPERATION"),
    ([[], [46, 45, 46, 47]], "SUSPEND_LIFT"),
    ([[46, 47, None], None], "SUSPEND_LIFT"),
])
def test_wind_branches(streams, expected):
    # Unread None sentinels in the final case prove suspension returns immediately.
    assert check_chairlift_anemometer(streams) == expected
