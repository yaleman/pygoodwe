
# Changelog

* 0.0.1 - 0.0.3 2019-10-09 Initial versions, basically just getting packaging and the most simple things working
* 0.0.4 2019-10-09 Fixed a bug that mis-identified the load generating power.
* 0.0.5 2019-10-09 Updated setup.py to build in a requirement for `requests`
* 0.0.6-0.0.7 2019-10-12 Updated SingleInverter to return battery state of charge, then fixed the fact I was implementing the same thing two different ways...
* 0.0.8 2019-10-12 I really should write some tests for this. Fixed SingleInverter.get_battery_soc() to actually work.
* 0.0.9 2019-10-12 Catching an error when the inverter data doesn't load.
* 0.0.10 ... not sure?
* 0.0.11 2019-11-05 Commented out some non-functional code.
* 0.0.12 2019-12-03 Removed the non-used code, fixed a bug.
* 0.0.13 2020-06-22 Added getPmeter from community submission, fixed a lot of pylint errors
* 0.0.14 2020-07-06 Updated API endpoint due to cert expiry/change of API from '<https://globalapi.sems.com.cn/api/>'' to '<https://semsportal.com/api/>' as the old one was throwing expired cert errors.
* 0.0.16 2021-02-04 Included option from Peter Verthez to download an Excel file of data, cleaned up some old code style mess.
* 0.0.17 2022-06-04 Fully typed, if a little janky, replaced flit packaging with uv run.
* 0.0.18 2022-06-28 Added mkdocs automagical documentation, bumped version to update details on pypi.
* 0.1.0 2022-10-05 Fixed issue with getDataPvoutput on SingleInverters. (#148)
* 0.1.2 2022-12-19 Updating SEMS API Endpoints to V2.
* 0.1.3 2022-12-29 Removed an extra error message.
* 0.1.4 2022-12-30 XLS Export fixes
* 0.1.5 2023-01-04 Fixes for get_current_readings to pass settings down properly, and do less double-error-handling.
* 0.1.7 2024-01-15 Adding login error handling and dependency updates.
* 0.1.9 2025-02-25 Moving to uv for package management.
