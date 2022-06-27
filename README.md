
# pygoodwe

A command line tool and python library to query the GOODWE SEMS Portal APIs.

## API Docs

Auto-generated documentation is here: https://yaleman.github.io/pygoodwe/

## Installation

You need to have Python 3 and pip installed. Then:

    python -m pip install pygoodwe

Determine the Station ID from the GOODWE site as follows. Open the [Sems Portal](https://www.semsportal.com). The Plant Status will reveal the Station ID in the URL. Example:

    https://www.semsportal.com/powerstation/powerstatussnmin/11112222-aaaa-bbbb-cccc-ddddeeeeeffff

Then the Station ID is `11112222-aaaa-bbbb-cccc-ddddeeeeeffff`.

## Contributions

Please feel free to lodge an [issue or pull request on GitHub](https://github.com/yaleman/pygoodwe/issues).

## Thanks

* Originally based off the work of [Mark Ruys and his gw2pvo software](https://github.com/markruys/gw2pvo) - I needed something more flexible, so I made this.

## Disclaimer

GOODWE access is based on the undocumented API used by mobile apps. This could break at any time.

## Example Code

Please check out test.py in the base of the repository for some simple example code.
