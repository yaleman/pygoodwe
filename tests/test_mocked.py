""" mocked tests """
import json
import os

import requests
import requests_mock


from pygoodwe import SingleInverter


def test_login_fail() -> None:
    fail_response_body = """{
  "hasError": false,
  "code": 100005,
  "msg": "Email or password error.",
  "data": null,
  "components": {
    "para": null,
    "langVer": 179,
    "timeSpan": 0,
    "api": "http://semsportal.com:85/api/v2/Common/CrossLogin",
    "msgSocketAdr": "https://eu-xxzx.semsportal.com"
  }
}"""
    # login detail don't matter as we're mocking it
    print("setting up api")
    goodwe = SingleInverter(
        system_id=os.getenv("GW_STATION_ID", "1"),
        account=os.getenv("GW_ACCOUNT", "thiswillnotwork"),
        password=os.getenv("GW_PASSWORD", "thiswillnotwork"),
        skipload=True,
    )

    print("setting up session mock")
    session = requests.Session()
    adapter = requests_mock.Adapter()
    session.mount("https://", adapter)

    adapter.register_uri(
        method="POST",
        url=goodwe.global_url + "v2/Common/CrossLogin",
        json=json.loads(fail_response_body),
        status_code=200,
    )
    goodwe.session = session

    login_result = goodwe.do_login()

    print(f"{login_result=}")
    print(f"{adapter.request_history=}")
    assert not login_result
