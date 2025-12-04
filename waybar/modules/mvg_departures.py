#!/usr/bin/python

import json
import requests
import time
import pydantic
from typing import Literal, Callable


class Info(pydantic.BaseModel):
    message: str
    type: str
    network: str


class Departure(pydantic.BaseModel):
    plannedDepartureTime: int
    realtime: bool
    delayInMinutes: int = 0
    realtimeDepartureTime: int
    transportType: Literal["UBAHN", "TRAM",
                           "SBAHN", "BUS", "REGIONAL_BUS", "BAHN"]
    label: str
    divaId: str
    network: str
    trainType: str
    destination: str
    cancelled: bool
    sev: bool
    platform: int | None = None
    platformChanged: bool | None = None
    messages: list[str]
    infos: list[Info]
    bannerHash: str
    occupancy: str
    stationGlobalId: str
    stopPointGlobalId: str
    lineId: str
    tripCode: int

    @pydantic.computed_field
    @property
    def formatted_label(self) -> str:
        if self.transportType in ["BUS", "REGIONAL_BUS"]:
            return f"Bus {self.label}"

        if self.transportType == "TRAM":
            return f"Tram {self.label}"

        return self.label

    @pydantic.computed_field
    @property
    def minutes_until_departure(self) -> int:
        return ((self.realtimeDepartureTime // 1000) - int(time.time())) // 60


def get_next_departures(station_global_id: str, amount: int) -> list[Departure]:
    res = requests.get(
        f"https://www.mvg.de/api/bgw-pt/v3/departures?globalId={station_global_id}&limit={amount}&transportTypes=UBAHN,TRAM,SBAHN,BUS,REGIONAL_BUS,BAHN")

    return [Departure(**d) for d in json.loads(res.text)]


def filter_departures(departures: list[Departure], filter: Callable[[Departure], bool]) -> list[Departure]:
    return [d for d in departures if filter(d)]


def main():
    GARCHING = "de:09184:490"  # Enter the API Global ID of your station here

    dep = get_next_departures(GARCHING, 10)

    current_time = int(time.time())
    dep = filter_departures(dep, lambda x: not x.cancelled)
    dep = filter_departures(
        dep, lambda x: x.realtimeDepartureTime // 1000 > current_time)

    next_departure: Departure = dep[0]

    text = f"{next_departure.formatted_label} - {next_departure.destination} ({next_departure.minutes_until_departure})"

    tooltip_lines = []
    tooltip_lines.append(
        f"Abfahrt um {time.strftime('%H:%M:%S', time.localtime(next_departure.realtimeDepartureTime//1000))}")

    if next_departure.platform:
        tooltip_lines.append(
            f"Abfahrt auf Bahnsteig {next_departure.platform}")

    tooltip_lines.append(f"Belegung: {next_departure.occupancy}")

    tooltip_lines.append("Nächste Abfahrten:")
    for i in range(1, 5):
        tooltip_lines.append(
            f"{dep[i].formatted_label} - {dep[i].destination} ({dep[i].minutes_until_departure})")

    print(json.dumps(
        {"text": text, "tooltip": "\n".join(tooltip_lines)}))


if __name__ == '__main__':
    main()
