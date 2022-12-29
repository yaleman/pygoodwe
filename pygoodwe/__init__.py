""" pygoodwe: a (terrible) interface to the goodwe solar API """


from datetime import date, datetime
import json
from json.decoder import JSONDecodeError
import logging
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Union

import requests
from requests.sessions import Session

__version__ = "0.0.17"

POWERFLOW_STATUS_TEXT = {
    -1: "Outward",
}
DEFAULT_UA = "PVMaster/2.0.4 (iPhone; iOS 11.4.1; Scale/2.00)"
API_URL = "https://semsportal.com/api/"


class API():
    """ API implementation """

    #pylint: disable=too-many-instance-attributes,too-many-arguments
    def __init__(
        self,
        system_id: str,
        account: str,
        password: str,
        api_url: str=API_URL,
        log_level: Optional[str]=None,
        user_agent: str=DEFAULT_UA,
        skipload: bool=False,
    ) -> None:
        """
        Options:

        skipload: don't run self.getCurrentReadings() on init
        api_url: you can change the API endpoint it hits
        """
        #TODO: lang: Real Soon Now it'll filter out any responses without that language

        if log_level is None:
            if "LOG_LEVEL" in os.environ:
                log_level = os.environ["LOG_LEVEL"]
            else:
                log_level = "INFO"

        if log_level in ("DEBUG", "INFO", "WARNING"):
            log_level = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
            logging.basicConfig(
                level=log_level,
            )
        self.session = Session()
        self.system_id = system_id
        self.account = account
        self.password = password
        self.token = '{"version":"v2.0.4","client":"ios","language":"en"}'
        self.global_url = api_url
        self.base_url = self.global_url

        logging.debug("API URL: %s", self.base_url)

        self.user_agent = user_agent

        if skipload:
            logging.debug("Skipping initial load of data")
            self.data: Dict[str, Any] = {}
        else:
            logging.debug("Doing load of data")
            self.getCurrentReadings(raw=True)

    def loaddata(self, filename: str) -> None:
        """ loads a json file of existing data """
        with open(filename, "r", encoding="utf8") as filehandle:
            self.data = json.loads(filehandle.read())

    _loaddata = loaddata

    def get_current_readings(
        self,
        raw: bool=True,
        retry: int=1,
        maxretries: int=5,
        delay: int=30,
    ) -> Dict[str, Any]:  # pylint: disable=invalid-name
        """ gets readings at the current point in time """
        payload = {"powerStationId": self.system_id}

        # GOODWE server
        self.data = self.call(
            "v2/PowerStation/GetMonitorDetailByPowerstationId", payload
        )

        retval = self.data

        if not self.data.get("inverter"):
            if retry < maxretries:
                logging.error(
                    "no inverter data, try %s, trying again in %s seconds", retry, delay
                )
                time.sleep(delay)
                return self.getCurrentReadings(
                    raw=raw, retry=retry + 1, maxretries=maxretries, delay=delay
                )
            logging.error("No inverter data after %s retries, quitting.", retry)
            sys.exit(f"No inverter data after {retry} retries, quitting.")
        return retval

    # stub function names to old names
    getCurrentReadings = get_current_readings

    # def getDayReadings(self, date):
    #     date_s = date.strftime('%Y-%m-%d')
    #     payload = {
    #         'powerStationId' : self.system_id
    #     }
    #     data = self.call("v2/PowerStation/GetMonitorDetailByPowerstationId", payload)
    #     if 'info' not in data:
    #     logging.warning(date_s + " - Received bad data " + str(data))
    #         return result
    #     result = {
    #         'latitude' : data['info'].get('latitude'),
    #         'longitude' : data['info'].get('longitude'),
    #         'entries' : []
    #     }
    #     payload = {
    #         'powerstation_id' : self.system_id,
    #         'count' : 1,
    #         'date' : date_s
    #     }
    #     data = self.call("PowerStationMonitor/GetPowerStationPowerAndIncomeByDay", payload)
    #     if len(data) == 0:
    #         logging.warning(date_s + " - Received bad data " + str(data))
    #         return result
    #     eday_kwh = data[0]['p']
    #     payload = {
    #         'id' : self.system_id,
    #         'date' : date_s
    #     }
    #     data = self.call("PowerStationMonitor/GetPowerStationPacByDayForApp", payload)
    #     if 'pacs' not in data:
    #         logging.warning(date_s + " - Received bad data " + str(data))
    #         return result
    #     minutes = 0
    #     eday_from_power = 0
    #     for sample in data['pacs']:
    #         parsed_date = datetime.strptime(sample['date'], "%m/%d/%Y %H:%M:%S")
    #         next_minutes = parsed_date.hour * 60 + parsed_date.minute
    #         sample['minutes'] = next_minutes - minutes
    #         minutes = next_minutes
    #         eday_from_power += sample['pac'] * sample['minutes']
    #     factor = eday_kwh / eday_from_power if eday_from_power > 0 else 1
    #     eday_kwh = 0
    #     for sample in data['pacs']:
    #         date += timedelta(minutes=sample['minutes'])
    #         pgrid_w = sample['pac']
    #         increase = pgrid_w * sample['minutes'] * factor
    #         if increase > 0:
    #             eday_kwh += increase
    #             result['entries'].append({
    #                 'dt' : date,
    #                 'pgrid_w': pgrid_w,
    #                 'eday_kwh': round(eday_kwh, 3)
    #             })
    #     return result

    @property
    def headers(self) -> Dict[str, str]:
        """ request headers """
        return {
            "User-Agent": self.user_agent,
            "Token": self.token,
        }

    # pylint: disable=invalid-name
    def getDayDetailedReadingsExcel(
        self,
        export_date: date,
        timeout: int=10,
        filename: Optional[str]=None,
    ) -> bool:
        """ retrieves the detailed daily results of the given date as an Excel sheet,
        processing the Excel sheet is outside the scope of the current module,
        possible args:
        - filename: the path where to write the output file, default "./Plant_Power_{datestr}.xls
        """
        datestr = datetime.strftime(export_date, "%Y-%m-%d")
        if filename is None:
            filename = f"Plant_Power_{datestr}.xls"
        logging.debug("Will write data for %s to file: %s", datestr, filename)

        uri = "v1/PowerStation/ExportPowerstationPac"
        # {"api":"v2/PowerStation/ExportPowerstationPac","param":{"date":"2021-12-20","pw_id":"<my-pw-id>"
        payload_export = {
            "date": datestr,
            "pw_id": self.system_id,
        }

        data = self.call(uri, payload=payload_export)


        payload_get_url = {
            "id": data
        }
        get_url_uri = "v1/ReportData/GetStationPowerDataFilePath"
        data = self.call(
            get_url_uri, payload=payload_get_url
        )

        file_url = data.get("file_path")
        if file_url is None:
            logging.error("Failed to get file path from ")
            return False

        response = requests.get(file_url, timeout=timeout)
        response.raise_for_status()

        try:
            file_download_path = Path(filename)
            file_download_path.write_bytes(response.content)
        except Exception as error_message:  # pylint: disable=broad-except
            logging.error(
                "Failed to write file %s! Error: %s", filename, error_message
            )
            return False
        return True


    def do_login(self, timeout: int = 10) -> bool:
        """ does the login and token saving thing """
        login_payload = {
            "account": self.account,
            "pwd": self.password,
        }
        try:
            response = self.session.post(
                self.global_url + "v2/Common/CrossLogin",
                headers=self.headers,
                data=login_payload,
                timeout=timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exp:
            logging.error("RequestException during do_login(): %s", exp)
            return False
        data = response.json()
        # logging.error(response.cookies)
        if data.get("api"):
            logging.debug("Setting base url to %s", data.get("api"))
            self.base_url = data.get("api")
        self.token = json.dumps(data.get("data"))
        logging.debug("Done login, token: %s", self.token)
        return True

    def call(
        self,
        url: str,
        payload: Any,
        max_tries: int = 3,
        timeout: int = 10,
    ) -> Dict[str, Any]:  # pylint: disable=unused-argument
        """ makes a call to the API """
        for i in range(1, max_tries):
            try:
                logging.debug(
                    "Pulling the following URL: base_url='%s', url='%s'",
                    self.base_url,
                    url,
                )
                response = self.session.post(
                    self.base_url + url,
                    headers=self.headers,
                    data=payload,
                    timeout=timeout,
                )
                response.raise_for_status()
                data = response.json()
                logging.debug("call response.json(): %s", json.dumps(data))

                # APIs return "success", "Success", "Successful" in the 'msg'
                # seen "Successful" in ExportPowerStationPac
                # logging.error("Msg result %s - %s", self.base_url + url, data.get('msg', ''))
                if data.get("msg", "").lower() in (
                    "success",
                    "successful",
                ) and "data" in data:  # pylint: disable=no-else-return
                    logging.debug(
                        "Returning data: %s", json.dumps(data["data"], default=str)
                    )
                    result: Dict[str, Any] = data.get("data")
                    return result
                logging.debug(json.dumps(data))

                logging.debug("Logging in again...")
                if not self.do_login():
                    logging.error("Failed to log in, bailing")
                    return {}
            except requests.exceptions.RequestException as exp:
                logging.error("RequestException: %s", exp)
            logging.debug("Sleeping for %s seconds...", i)
            time.sleep(i)

        logging.error("Failed to call GoodWe API url='%s'", self.base_url + url)
        return {}

    @classmethod
    def parseValue(cls, value: str, unit: str) -> float:  # pylint: disable=invalid-name
        """ takes a string value and reutrns it as a float (if possible) """
        try:
            return float(value.rstrip(unit))
        except ValueError as exp:
            logging.warning("ValueError: %s", exp)
            return 0.0

    def are_batteries_full(self, fullstate: float = 100.0) -> bool:
        """boolean result for if the batteries are full. you can set your given 'full'
        percentage in float if you want to lower this a little
        are_batteries_full(fullstate=90.0): returns bool
        """
        for battery in self.get_batteries_soc():
            if battery < fullstate:
                return False
        return True

    def _get_batteries_soc(self) -> List[float]:
        """returns a list of the state of charge for the batteries
        returns: list[float,]
        """
        if not self.data:
            self.getCurrentReadings()
        if "inverter" not in self.data:
            raise ValueError("Couldn't get data...")
        return [
            float(inverter.get("invert_full", {}).get("soc"))
            for inverter in self.data["inverter"]
        ]

    def get_batteries_soc(self) -> List[float]:
        """ return the battery state of charge """
        return self._get_batteries_soc()

    def getPVFlow(self) -> float:  # pylint: disable=invalid-name
        """ PV flow data """
        raise NotImplementedError("SingleInverter has this, multi does not")

    def getVoltage(self) -> List[float]:  # pylint: disable=invalid-name
        """ returns the a list of the first AC channel voltages """
        if not self.data:
            self.getCurrentReadings(True)
        if "inverter" not in self.data:
            raise ValueError("Couldn't get data...")
        return [
            float(inverter.get("invert_full", {}).get("vac1"))
            for inverter in self.data["inverter"]
        ]

    def getPmeter(self) -> float:  # pylint: disable=invalid-name
        """ gets the current line pmeter """
        if not self.data:
            self.getCurrentReadings()
        return float(self.data.get("inverter", {}).get("invert_full", {}).get("pmeter"))

    def getLoadFlow(self) -> List[float]:  # pylint: disable=invalid-name
        """ returns the list of inverter multi-unit load watts """
        raise NotImplementedError("multi-unit load watts isn't implemented yet")

    def get_inverter_temperature(self) -> List[float]:
        """ returns the list of inverter temperatures """
        if not self.data:
            self.get_current_readings(True)
        if "inverter" not in self.data:
            raise ValueError("Couldn't get data...")
        return [
            float(inverter.get("invert_full", {}).get("tempperature"))
            for inverter in self.data["inverter"]
        ]

    def getDataPvoutput(
        self
        ) -> Dict[str, Union[str, float]]:  # pylint: disable=invalid-name
        """updates and returns the data necessary for a one-shot pvoutput upload
        'd' : testdate.strftime("%Y%m%d"),
        't' : testtime.strftime("%H:%M"),
        'v2' : 500, # power generation
        'v4' : 450,
        'v5' : 23.5, # temperature
        'v6' : 234.0, # voltage
        """
        if not self.data:
            self.getCurrentReadings()
        # "time": "10/04/2019 14:37:29"
        timestamp = datetime.strptime(
            self.data.get("info", {}).get("time"), "%m/%d/%Y %H:%M:%S"
        )
        data: Dict[str, Union[str, float]] = {}
        data["d"] = timestamp.strftime("%Y%m%d")  # date
        data["t"] = timestamp.strftime("%H:%M")  # time
        data["v2"] = self.getPVFlow()  # PV Generation
        data["v4"] = self.getLoadFlow()[0]  # power consumption
        data["v5"] = self.get_inverter_temperature()[0]  # inverter temperature
        data["v6"] = self.getVoltage()[0]  # voltage
        return data


class SingleInverter(API):
    """ API implementation for an account with a single inverter """
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        system_id: str,
        account: str,
        password: str,
        api_url: str=API_URL,
        log_level: Optional[str]=None,
        user_agent: str=DEFAULT_UA,
        skipload: bool=False,
        ) -> None:
        self.loadflow = 0.0
        self.loadflow_direction = ""

        self.data: Dict[str, Any]

        # instantiate the base class
        super().__init__(system_id, account, password, api_url, log_level, user_agent, skipload)

    def loaddata(self, filename: str) -> None:
        """ loads the ata from a given file """
        self._loaddata(filename)
        if self.data.get("inverter"):
            self.data["inverter"] = self.data["inverter"][0]

    def get_current_readings(
        self,
        raw: bool=True,
        retry: int=1,
        maxretries: int=5,
        delay: int=30,
        ) -> Any:
        """ grabs the data and makes sure self.data only has a single inverter """
        # update the data
        super().get_current_readings(raw)
        # reduce self.data['inverter'] to a single dict from a list
        retval = None
        if self.data.get("inverter"):
            self.data["inverter"] = self.data["inverter"][0]
        else:
            if retry < maxretries:
                logging.error(
                    "no inverter data, try %s, trying again in %s seconds", retry, delay
                )
                time.sleep(delay)
                return self.get_current_readings(
                    raw=raw, retry=retry + 1, maxretries=maxretries, delay=delay
                )
            logging.error("No inverter data after %s retries, quitting.", retry)
            sys.exit(f"No inverter data after {retry} retries, quitting.")
        return retval
    getCurrentReadings = get_current_readings

    def _get_station_location(self) -> Dict[str, Union[str, int]]:
        """ gets the identified lat and long from the station data """
        return self.get_station_location()

    def get_station_location(self) -> Dict[str, Union[str, int]]:
        """ gets the identified lat and long from the station data """
        if not self.data:
            self.getCurrentReadings()
        return {
            "latitude": self.data.get("info", {}).get("latitude"),
            "longitude": self.data.get("info", {}).get("longitude"),
        }

    def getPVFlow(self) -> float:
        """ returns the current flow amount of the PV panels """
        if not self.data:
            self.getCurrentReadings()
        if self.data["powerflow"]["pv"].endswith("(W)"):
            pvflow = self.data["powerflow"]["pv"][:-3]
        else:
            pvflow = self.data["powerflow"]["pv"]
        return float(pvflow)

    def getVoltage(self) -> float: #type: ignore
        """ gets the current line voltage """
        if not self.data:
            self.getCurrentReadings()
        return float(self.data["inverter"]["invert_full"]["vac1"])

    def get_day_income(self) -> float:
        """ gets the current daily income """
        if not self.data:
            self.getCurrentReadings()
        return float(self.data['kpi']['day_income'])

    def get_total_income(self) -> float:
        """ gets the total income """
        if not self.data:
            self.getCurrentReadings()
        return float(self.data['kpi']['total_income'])

    def get_total_power(self) -> float:
        """ gets the total power generated"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data['kpi']['total_power'])

    def get_day_power(self) -> float:
        """ gets the total power generated"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data['kpi']['power'])

    def getLoadFlow(self) -> float: # type: ignore
        if not self.data:
            self.getCurrentReadings()
        if self.data["powerflow"]["bettery"].endswith("(W)"):
            loadflow = float(self.data["powerflow"]["load"][:-3])
        else:
            loadflow = float(self.data["powerflow"]["load"])
        # I'd love to see the *house* generate power
        if self.data["powerflow"]["loadStatus"] == -1:
            loadflow_direction = "Importing"
        elif self.data["powerflow"]["loadStatus"] == 1:
            loadflow_direction = "Using Battery"
        else:
            raise ValueError(
                f"Your 'load' is doing something odd - status is '{self.data['powerflow']['loadStatus']}''."
            )  # pylint: disable=line-too-long
        self.loadflow = loadflow
        self.loadflow_direction = loadflow_direction
        return loadflow

    def _get_batteries_soc(self) -> float: #type: ignore
        """returns the state of charge of the battery"""
        if not self.data:
            self.getCurrentReadings()
        if not self.data.get("soc", False):
            raise ValueError("No state of charge available from data")
        return float(self.data["soc"].get("power"))

    def get_battery_soc(self) -> float:
        """returns the single value state of charge for the batteries in the plant
        returns : float
        """
        return self._get_batteries_soc()

    def get_inverter_temperature(self) -> float: #type: ignore
        if not self.data:
            self.get_current_readings(True)
        return float(self.data["inverter"]["tempperature"])

    def getDataPvoutput(
        self
        ) -> Dict[str, Union[str, float]]:  # pylint: disable=invalid-name
        """updates and returns the data necessary for a one-shot pvoutput upload
        'd' : testdate.strftime("%Y%m%d"),
        't' : testtime.strftime("%H:%M"),
        'v2' : 500, # power generation
        'v4' : 450,
        'v5' : 23.5, # temperature
        'v6' : 234.0, # voltage
        """
        if not self.data:
            self.getCurrentReadings()
        # "time": "10/04/2019 14:37:29"
        timestamp = datetime.strptime(
            self.data.get("info", {}).get("time"), "%m/%d/%Y %H:%M:%S"
        )
        data: Dict[str, Union[str, float]] = {}
        data["d"] = timestamp.strftime("%Y%m%d")  # date
        data["t"] = timestamp.strftime("%H:%M")  # time
        data["v2"] = self.getPVFlow()  # PV Generation
        data["v4"] = self.getLoadFlow()  # power consumption
        data["v5"] = self.get_inverter_temperature()  # inverter temperature
        data["v6"] = self.getVoltage()  # voltage
        return data
