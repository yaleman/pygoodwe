
# pygoodwe

A command line tool and python library to query the GOODWE SEMS Portal APIs.

![travis-ci build status](https://travis-ci.org/yaleman/pygoodwe.svg?branch=master)

## Installation

You need to have Python 3 and pip installed. Then:

    sudo pip3 install pygoodwe

Determine the Station ID from the GOODWE site as follows. Open the [Sems Portal](https://www.semsportal.com). The Plant Status will reveal the Station ID in the URL. Example:

    https://www.semsportal.com/powerstation/powerstatussnmin/11112222-aaaa-bbbb-cccc-ddddeeeeeffff

Then the Station ID is `11112222-aaaa-bbbb-cccc-ddddeeeeeffff`.

## Contributions

Please feel free to lodge an [issue or pull request on GitHub](https://github.com/yaleman/pygoodwe/issues).

## Thanks

* Based heavily off the work of [Mark Ruys and his gw2pvo software](https://github.com/markruys/gw2pvo) - I needed something more flexible, so I made this.

## Disclaimer

GOODWE access is based on the undocumented API used by mobile apps. This could break at any time.

# Version history

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