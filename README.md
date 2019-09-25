
# pygoodwe

A command line tool and python library to query the GOODWE SEMS Portal APIs.

## Installation

You need to have Python 3 and pip installed. Then:

    sudo pip3 install pygoodwe

Determine the Station ID from the GOODWE site as follows. Open the [Sems Portal](https://www.semsportal.com). The Plant Status will reveal the Station ID in the URL. Example:

    https://www.semsportal.com/powerstation/powerstatussnmin/11112222-aaaa-bbbb-cccc-ddddeeeeeffff

Then the Station ID is `11112222-aaaa-bbbb-cccc-ddddeeeeeffff9a6415bf-cdcc-46af-b393-2b442fa89a7f`.

## Thanks

* Based heavily off the work of [Mark Ruys and his gw2pvo software](https://github.com/markruys/gw2pvo) - I needed something more flexible, so I made this.

## Disclaimer

GOODWE access is based on the undocumented API used by mobile apps. This could break at any time.