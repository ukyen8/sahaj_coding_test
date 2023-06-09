"""Test suite for `src.flights`."""

# Standard library
import os
import pathlib
import typing

# Third-party
import pydantic
import pytest

# First-party
import src.typings
from src.flights import (
    gen_discount_code,
    get_flight_ticket_data,
    handle_errors,
    output_invalid_flight_ticket_data,
    output_valid_flight_ticket_data,
    validate_flight_ticket_data,
)
from src.models import FlightTicket

BASE_OUTPUT_HEADERS = (
    "First_name,Last_name,PNR,Fare_class,Travel_date,Pax,"
    + "Ticketing_date,Email,Mobile_phone,Booked_cabin"
)


def test_get_flight_ticket_data(
    sample_flight_ticket_data_path: pathlib.Path,
) -> None:
    """Assert method processes input csv file correctly."""
    ticket_data = get_flight_ticket_data(sample_flight_ticket_data_path)
    assert len(ticket_data) == 9
    assert ticket_data[0]["Email"] == "abhishek@zzz.com"
    assert ticket_data[0]["First_name"] == "Abhishek"


def test_get_flight_ticket_data__error() -> None:
    """Assert method raises error if file is not found."""
    with pytest.raises(FileNotFoundError):
        get_flight_ticket_data(pathlib.Path("non_existent_file.csv"))


def test_handle_error(
    sample_flight_ticket_data: dict[str, object],
    invalid_flight_ticket_data: dict[str, object],
) -> None:
    """Assert method returns expected error codes."""
    try:
        FlightTicket(**invalid_flight_ticket_data)  # type: ignore[arg-type]
    except pydantic.ValidationError as exc:
        error_codes = handle_errors(exc)
        assert error_codes == (
            "Invalid PNR,Invalid ticketing date,"
            + "Invalid email,Invalid phone number,Invalid Booked_cabin"
        )


@pytest.mark.parametrize(
    ("fare_class", "expected_discount_code"),
    [
        ("A", "OFFER_20"),
        ("E", "OFFER_20"),
        ("F", "OFFER_30"),
        ("K", "OFFER_30"),
        ("L", "OFFER_25"),
        ("R", "OFFER_25"),
        ("Z", ""),
    ],
)
def test_gen_discount_code(
    fare_class: str, expected_discount_code: str
) -> None:
    """Assert method returns correct discount code."""
    assert gen_discount_code(fare_class) == expected_discount_code


def test_validate_flight_ticket_data(
    sample_flight_ticket_data: src.typings.FlightTicket,
    invalid_flight_ticket_data: src.typings.FlightTicket,
) -> None:
    """Assert method validates flight ticket data correctly."""
    valid_flight_ticket, invalid_flight_ticket = validate_flight_ticket_data(
        [sample_flight_ticket_data, invalid_flight_ticket_data]
    )
    assert len(valid_flight_ticket) == 1
    assert "Discount_code" in valid_flight_ticket[0]
    assert len(invalid_flight_ticket) == 1
    assert "Error" in invalid_flight_ticket[0]


@pytest.mark.parametrize(
    (
        "method",
        "flight_ticket_data",
        "file_name",
        "new_header",
        "new_column_value",
    ),
    [
        (
            output_valid_flight_ticket_data,
            pytest.lazy_fixture("sample_flight_ticket_data"),  # type: ignore[operator] # noqa: E501
            "valid-flight-tickets",
            "Discount_code",
            "OFFER_20",
        ),
        (
            output_invalid_flight_ticket_data,
            pytest.lazy_fixture("invalid_flight_ticket_data"),  # type: ignore[operator] # noqa: E501
            "invalid-flight-tickets",
            "Error",
            "Invalid email",
        ),
    ],
)
def test_output_valid_and_invalid_flight_ticket_data(
    method: typing.Callable[[list[src.typings.FlightTicket], str], str | None],
    flight_ticket_data: src.typings.FlightTicket,
    file_name: str,
    new_header: str,
    new_column_value: str,
    tmp_path: pathlib.Path,
) -> None:
    """Assert method outputs valid flight ticket data correctly."""
    full_path = tmp_path / file_name
    flight_ticket_data[new_header] = new_column_value
    output_file = method([flight_ticket_data], str(full_path))
    assert output_file
    assert os.path.exists(output_file)
    output_file = method([flight_ticket_data], str(full_path))
    assert output_file
    assert os.path.exists(output_file)
    with open(f"{output_file}") as file:
        headers = file.readline().strip()
    assert headers == f"{BASE_OUTPUT_HEADERS},{new_header}"
