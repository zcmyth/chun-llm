import googlemaps
import os
import json
from typing import Protocol
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class Status(Enum):
    OK = 1
    INVALID_INPUT = 2


@dataclass
class PluginResult:
    """
    Class for the plugin result. The same as LLM model response
    """

    status: Status
    details: str


class Plugin(Protocol):
    """
    A plugin can be imported into the engine to
    perform some specific tasks.
    """

    def name(self):
        """
        The name of the plugin, no space.
        """
        ...

    def description(self):
        """
        The description of this plugin.
        It will be used by LLM to dispatch requests to different plugins.
        """
        ...

    def input_schema(self):
        """
        Returns the json schema to describe the input of this plugin

        """
        ...

    def run(self, input):
        """
        Executes the plugin with given input.
        """


class DistanceResult:
    """
    A wrapper class to make it easy to access the response from Google map API
    """

    def __init__(self, raw):
        self._raw = raw

    def _first_row(self):
        return self._raw["rows"][0]["elements"][0]

    def has_result(self):
        return self._first_row()["status"] == "OK"

    def origin(self):
        return self._raw["origin_addresses"][0]

    def destination(self):
        return self._raw["destination_addresses"][0]

    def result(self):
        row = self._first_row()
        return {
            "from": self.origin(),
            "to": self.destination(),
            "distance": row["distance"]["text"],
            "duration": row["duration"]["text"],
        }

    def describe_error(self):
        missing = "origin" if not self.origin() else "destination"
        return f"The {missing} address is ambiguous, please ask users to provide more information to clarify."


class TravelDistancePlugin:

    def __init__(self):
        self._gmaps = googlemaps.Client(key=os.environ.get("GOOGLE_MAP_API_KEY"))

    def name(self):
        return "travel_distance"

    def description(self):
        return "Help users to find travel time between two places"

    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "travel_mode": {
                    "type": "string",
                    "enum": ["driving", "bicycling", "walking", "transit"],
                },
            },
            "required": ["origin", "destination", "travel_mode"],
        }

    def run(self, input):
        raw_response = self._gmaps.distance_matrix(
            [input["origin"]],
            [input["destination"]],
            mode=input["travel_mode"],
            departure_time=datetime.now(),
            traffic_model="optimistic",
        )
        result = DistanceResult(raw_response)
        if result.has_result():
            return PluginResult(status=Status.OK, details=json.dumps(result.result()))
        return PluginResult(
            status=Status.INVALID_INPUT, details=result.describe_error()
        )


class WeatherPlugin:
    def name(self):
        return "get_weather"

    def description(self):
        return "Get the current weather in a given location"

    def input_schema(self):
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },
            "required": ["location"],
        }

    def run(self, input):
        return PluginResult(status=Status.OK, details="Raining")


def get_plugins():
    return [TravelDistancePlugin(), WeatherPlugin()]
