
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
* 0.0.14 2020-07-06 Updated API endpoint due to cert expiry/change of API from 'https://globalapi.sems.com.cn/api/'' to 'https://semsportal.com/api/' as the old one was throwing expired cert errors.
* 0.0.16 2021-02-04 Included option from Peter Verthez to download an Excel file of data, cleaned up some old code style mess.
* 0.0.17 2022-06-04 Fully typed, if a little janky, replaced flit packaging with poetry.
* 0.0.18 2022-06-28 Added mkdocs automagical documentation, bumped version to update details on pypi.
