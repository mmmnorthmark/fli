"""Security-focused input limits for MCP tools."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from fli.mcp.server import (
    MAX_DATE_SEARCH_RANGE_DAYS,
    MAX_PASSENGERS,
    MAX_TRIP_DURATION_DAYS,
    DateSearchParams,
    FlightSearchParams,
    search_dates,
)


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


def test_date_search_rejects_ranges_over_budget():
    start_date = _future(30)
    end_date = (
        date.fromisoformat(start_date) + timedelta(days=MAX_DATE_SEARCH_RANGE_DAYS)
    ).isoformat()

    with pytest.raises(ValidationError, match="date range"):
        DateSearchParams(
            origin="JFK",
            destination="LHR",
            start_date=start_date,
            end_date=end_date,
        )


def test_search_dates_rejects_oversized_range_before_network():
    start_date = _future(30)
    end_date = (
        date.fromisoformat(start_date) + timedelta(days=MAX_DATE_SEARCH_RANGE_DAYS)
    ).isoformat()

    with patch("fli.mcp.server.SearchDates.search") as search:
        with pytest.raises(ValidationError, match="date range"):
            search_dates(
                origin="JFK",
                destination="LHR",
                start_date=start_date,
                end_date=end_date,
            )

    search.assert_not_called()


def test_date_search_rejects_excessive_trip_duration():
    with pytest.raises(ValidationError, match="less than or equal"):
        DateSearchParams(
            origin="JFK",
            destination="LHR",
            start_date=_future(30),
            end_date=_future(60),
            trip_duration=MAX_TRIP_DURATION_DAYS + 1,
        )


def test_flight_search_rejects_excessive_passenger_count():
    with pytest.raises(ValidationError, match="less than or equal"):
        FlightSearchParams(
            origin="JFK",
            destination="LHR",
            departure_date=_future(30),
            passengers=MAX_PASSENGERS + 1,
        )


def test_flight_search_rejects_too_many_origin_codes():
    with pytest.raises(ValidationError, match="At most 5 airport codes"):
        FlightSearchParams(
            origin="JFK,LGA,EWR,BOS,PHL,DCA",
            destination="LHR",
            departure_date=_future(30),
        )


def test_flight_search_rejects_return_before_departure():
    with pytest.raises(ValidationError, match="return_date"):
        FlightSearchParams(
            origin="JFK",
            destination="LHR",
            departure_date=_future(40),
            return_date=_future(30),
        )
