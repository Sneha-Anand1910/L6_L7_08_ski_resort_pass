"""Statement coverage targets; expected values derived from source, not execution."""
import pytest
from ski_resort_pass import process_resort_bookings, check_chairlift_anemometer


def group(duration="full_day", skiers=None, **options):
    return dict(is_active=True, duration=duration,
                skiers=[] if skiers is None else skiers, **options)


@pytest.mark.parametrize("groups,fee", [(None, 0), ({}, 0), ((), 0), ("bad", 0), (42, 0), ([], -0.01)])
def test_invalid_arguments(groups, fee):
    with pytest.raises(ValueError, match="^Invalid groups list or facility fee$"):
        process_resort_bookings(groups, fee)


@pytest.mark.parametrize("groups", [[], [{}], [{"is_active": False}], [group()],
                                      [group("unknown")]])
def test_zero_sales(groups):
    assert process_resort_bookings(groups, 15) == {"total_revenue": 0.0, "status": "ZERO_SALES"}


@pytest.mark.parametrize("duration,age,expected", [
    ("full_day", 1, 48.0), ("full_day", 11, 48.0),
    ("full_day", 12, 80.0), ("full_day", 64, 80.0),
    ("full_day", 65, 56.0), ("full_day", 90, 56.0),
    ("half_day", 11, 30.0), ("half_day", 30, 50.0), ("half_day", 65, 35.0),
    ("season", 11, 180.0), ("season", 30, 300.0), ("season", 65, 210.0),
])
def test_pass_prices(duration, age, expected):
    assert process_resort_bookings([group(duration, [{"age": age}])], 0) == {
        "total_revenue": expected, "status": "COMPLETED"}


@pytest.mark.parametrize("rental,locker,expected", [
    (False, False, 80.0), (True, False, 115.0),
    (False, True, 95.0), (True, True, 130.0),
])
def test_optional_charges(rental, locker, expected):
    groups = [group(skiers=[{"age": 30, "gear_rental": rental}], includes_lodge_locker=locker)]
    assert process_resort_bookings(groups, 15) == {"total_revenue": expected, "status": "COMPLETED"}


def test_invalid_ages_skip_rental_and_continue():
    skiers = [{"age": 0, "gear_rental": True}, {"age": -1}, {}, {"age": 30}]
    assert process_resort_bookings([group(skiers=skiers)], 0) == {
        "total_revenue": 80.0, "status": "COMPLETED"}


@pytest.mark.parametrize("duration,age,rental,expected", [
    ("full_day", 11, False, 40.0), ("season", 65, True, 185.0),
])
def test_blackout_overrides_age_discount(duration, age, rental, expected):
    skiers = [{"age": age, "gear_rental": rental, "blackout_override": True}]
    assert process_resort_bookings([group(duration, skiers)], 0) == {
        "total_revenue": expected, "status": "COMPLETED"}


@pytest.mark.parametrize("locker,expected,status", [(False, 0.0, "ZERO_SALES"), (True, 15.0, "COMPLETED")])
def test_half_day_cancellation(locker, expected, status):
    skiers = [{"age": 30, "gear_rental": True},
              {"age": 30, "blackout_override": True, "gear_rental": True},
              {"age": 30}]
    assert process_resort_bookings([group("half_day", skiers, includes_lodge_locker=locker)], 15) == {
        "total_revenue": expected, "status": status}


@pytest.mark.parametrize("count,status", [(4, "ZERO_SALES"), (5, "AUDIT_REVIEW")])
def test_rejection_threshold(count, status):
    assert process_resort_bookings([group(skiers=[{"age": 0}] * count)], 0) == {
        "total_revenue": 0.0, "status": status}


def test_multiple_groups_and_rounding_with_audit():
    groups = [group("bad") for _ in range(5)]
    groups += [{"is_active": False, "duration": "season", "skiers": [{"age": 30}]},
               group(skiers=[{"age": 11}, {"age": 65, "gear_rental": True}], includes_lodge_locker=True),
               group("half_day", [{"age": 30}])]
    # 48 + 56 + 35 + 10.126 + 50 = 199.126.
    assert process_resort_bookings(groups, 10.126) == {"total_revenue": 199.13, "status": "AUDIT_REVIEW"}


def test_default_duration_and_completed_rounding():
    groups = [{"is_active": True, "skiers": [{"age": 30}], "includes_lodge_locker": True}]
    assert process_resort_bookings(groups, 0.126) == {"total_revenue": 80.13, "status": "COMPLETED"}


@pytest.mark.parametrize("streams,expected", [
    ([], "NO_DATA"), ([[]], "SAFE_OPERATION"), ([[], []], "SAFE_OPERATION"),
    ([[0, 30, 45]], "SAFE_OPERATION"), ([[46]], "SAFE_OPERATION"),
    ([[46, 47]], "SUSPEND_LIFT"), ([[46, 45, 47]], "SAFE_OPERATION"),
    ([[46, 20, 47, 48]], "SUSPEND_LIFT"),
    ([[46], [47]], "SAFE_OPERATION"), ([[], [30], [46, 47]], "SUSPEND_LIFT"),
])
def test_wind_readings(streams, expected):
    assert check_chairlift_anemometer(streams) == expected
