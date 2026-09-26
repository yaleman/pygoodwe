
# pygoodwe

A command line tool and Python library to query GoodWe SEMS+ live readings.

## API Docs

Auto-generated documentation is here: <https://yaleman.github.io/pygoodwe/>

## Installation

You need to have Python 3 and pip installed. Then:

    python -m pip install pygoodwe

Find the station ID in your SEMS+ station URL. Existing Classic station IDs can also be used if the station was migrated. For example, a Classic URL contained the ID here:

    https://www.semsportal.com/powerstation/powerstatussnmin/11112222-aaaa-bbbb-cccc-ddddeeeeeffff

Then the Station ID is `11112222-aaaa-bbbb-cccc-ddddeeeeeffff`.

## SEMS+ behavior

`API` and `SingleInverter` keep their existing constructor and reading methods. Live readings use SEMS+ Web only. SEMS+ combines station flow, device status, telemetry, and energy counters into the existing `data` layout. The `info.time` value is the local retrieval time because the sampled flow response does not provide a station timestamp. Missing or permission-restricted fields are left absent; they are not replaced with zero. In particular, station location, income, and some inverter measurements may be unavailable to existing getters. SEMS+ authentication or reading errors are reported directly without attempting the retired Classic backend.

The `api_url` and `user_agent` constructor arguments remain accepted for source compatibility but do not override SEMS+ routing or headers. SEMS+ uses its own login URL and the gateway URL returned by login. `getPowerStationPowerReportByMonth`, `getDayDetailedReadingsExcel`, and the old route-level `call` method remain callable but raise `NotImplementedError` immediately; SEMS+ equivalents are outside the current live-readings update.

SEMS+ is an undocumented GoodWe API. A read-only account can retrieve available monitoring values; no remote-control permission is required by this library.

To use example.py or the other examples, copy config.py.example to config.py and add your details.

## Contributions

Please feel free to lodge an [issue or pull request on GitHub](https://github.com/yaleman/pygoodwe/issues).

## Thanks

* Originally based off the work of [Mark Ruys and his gw2pvo software](https://github.com/markruys/gw2pvo) - I needed something more flexible, so I made this.

## Disclaimer

GOODWE access is based on the undocumented API used by mobile apps. This could break at any time.

## Example Code

Please check out example.py or the examples folder in [the project repository](https://github.com/yaleman/pygoodwe) for some simple example code.
