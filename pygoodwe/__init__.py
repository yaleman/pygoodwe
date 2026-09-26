"""pygoodwe: a (terrible) interface to the goodwe solar API"""

import json
import logging
import os
import time
from datetime import date, datetime
from typing import Any

from requests.sessions import Session

from .sems_plus import GATEWAY_URL, WEB_USER_AGENT, FailureKind, SemsPlusClient, SemsPlusError

__version__ = "0.0.17"

POWERFLOW_STATUS_TEXT = {
    -1: "Outward",
}
DEFAULT_UA = WEB_USER_AGENT
API_URL = GATEWAY_URL


class API:
    """API implementation"""

    def __init__(
        self,
        system_id: str,
        account: str,
        password: str,
        api_url: str = API_URL,
        log_level: str | None = None,
        user_agent: str = DEFAULT_UA,
        skipload: bool = False,
    ) -> None:
        """
        Options:

        skipload: don't run self.getCurrentReadings() on init
        api_url and user_agent are retained for constructor compatibility.
        SEMS+ selects its authenticated gateway and request headers.
        """
        # TODO: lang: Real Soon Now it'll filter out any responses without that language

        self.data: dict[str, Any] = {}

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
        self.logger = logging.getLogger(__name__)
        self.session = Session()
        self._sems_plus: SemsPlusClient | None = None
        self.system_id = system_id
        self.account = account
        self.password = password
        self.token = ""
        self.global_url = api_url
        self.base_url = self.global_url

        self.user_agent = user_agent

        if skipload:
            self.logger.debug("Skipping initial load of data")
        else:
            self.logger.debug("Doing load of data")
            self.getCurrentReadings(raw=True)

    def loaddata(self, filename: str) -> None:
        """loads a json file of existing data"""
        with open(filename, "r", encoding="utf8") as filehandle:
            self.data = json.loads(filehandle.read())

    _loaddata = loaddata

    def get_current_readings(
        self,
        raw: bool = True,
        retry: int = 1,
        maxretries: int = 5,
        delay: int = 30,
    ) -> dict[str, Any]:
        """gets readings at the current point in time"""
        client = self._web_client()
        while True:
            try:
                self.data = client.readings(self.system_id)
                break
            except SemsPlusError as exc:
                if exc.kind is not FailureKind.NO_INVERTERS or retry >= maxretries:
                    raise
                self.logger.warning("SEMS+ returned no inverters; retrying in %s seconds", delay)
                time.sleep(delay)
                retry += 1
        self.token = json.dumps(client.token)
        self.base_url = client.api_base
        return self.data

    # stub function names to old names
    getCurrentReadings = get_current_readings

    @property
    def headers(self) -> dict[str, str]:
        """Authenticated SEMS+ headers, excluding the changing signature."""
        token = self._web_client().token
        return {"User-Agent": WEB_USER_AGENT, "Token": json.dumps(token) if token is not None else ""}

    def getDayDetailedReadingsExcel(
        self,
        export_date: date,
        timeout: int = 10,
        filename: str | None = None,
    ) -> bool:
        """Retained interface; SEMS+ Excel export is not implemented."""
        raise NotImplementedError("SEMS+ daily Excel export is not implemented")

    def getPowerStationPowerReportByMonth(
        self,
        report_date: date,
        page_index: int = 1,
        page_size: int = 8,
    ) -> dict[str, Any] | None:
        """Retained interface; SEMS+ monthly reports are not implemented."""
        raise NotImplementedError("SEMS+ monthly reports are not implemented")

    def _web_client(self) -> SemsPlusClient:
        if self._sems_plus is None or self._sems_plus.session is not self.session:
            self._sems_plus = SemsPlusClient(self.session, self.account, self.password, self.logger)
        return self._sems_plus

    def do_login(self, timeout: int = 10) -> bool:
        """Authenticate with SEMS+ Web."""
        try:
            client = self._web_client()
            client.login(timeout)
            self.token = json.dumps(client.token)
            self.base_url = client.api_base
            return True
        except SemsPlusError as exc:
            if exc.kind is FailureKind.RATE_LIMIT:
                raise
            self.logger.error("SEMS+ login failed (%s)", exc.kind.value)
            return False

    def call(
        self,
        url: str,
        payload: Any,
        max_tries: int = 3,
        timeout: int = 10,
    ) -> dict[str, Any]:
        """Retained interface; Classic route calls have no SEMS+ equivalent."""
        raise NotImplementedError("Classic API routes are no longer supported")

    def parseValue(self, value: str, unit: str) -> float:
        """takes a string value and reutrns it as a float (if possible)"""
        try:
            return float(value.rstrip(unit))
        except ValueError as exp:
            self.logger.warning("ValueError: %s", exp)
            return 0.0

    def are_batteries_full(self, fullstate: float = 100.0) -> bool:
        """boolean result for if the batteries are full. you can set your given 'full'
        percentage in float if you want to lower this a little
        are_batteries_full(fullstate=90.0): returns bool
        """
        soc = self.get_batteries_soc()
        if not isinstance(soc, list):
            return soc >= fullstate

        for battery in soc:
            if battery < fullstate:
                return False
        return True

    def _get_batteries_soc(self) -> list[float] | float:
        """returns a list of the state of charge for the batteries"""
        if not self.data:
            self.getCurrentReadings()
        if "inverter" not in self.data:
            raise ValueError("Couldn't get data...")
        values = [inverter.get("invert_full", {}).get("soc") for inverter in self.data["inverter"]]
        if any(value is None for value in values):
            raise ValueError("Per-inverter state of charge is unavailable")
        return [float(value) for value in values]

    def get_batteries_soc(self) -> list[float] | float:
        """return the battery state of charge"""
        return self._get_batteries_soc()

    def getPVFlow(self) -> float:
        """PV flow data"""
        raise NotImplementedError("SingleInverter has this, multi does not")

    def getVoltage(self) -> list[float] | float:
        """returns the a list of the first AC channel voltages"""
        if not self.data:
            self.getCurrentReadings(True)
        if "inverter" not in self.data:
            raise ValueError("Couldn't get data...")
        return [float(inverter.get("invert_full", {}).get("vac1")) for inverter in self.data["inverter"]]

    def getPmeter(self) -> float:
        """gets the current line pmeter"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data.get("inverter", {}).get("invert_full", {}).get("pmeter"))

    def getLoadFlow(self) -> list[float] | float:
        """returns the list of inverter multi-unit load watts"""
        raise NotImplementedError("multi-unit load watts isn't implemented yet")

    def get_inverter_temperature(self) -> list[float] | float:
        """returns the list of inverter temperatures"""
        if not self.data:
            self.get_current_readings(True)
        if "inverter" not in self.data:
            raise ValueError("Couldn't get data...")
        return [float(inverter.get("invert_full", {}).get("tempperature")) for inverter in self.data["inverter"]]

    def getDataPvoutput(
        self,
    ) -> dict[str, str | float]:
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
        timestamp = datetime.strptime(self.data.get("info", {}).get("time"), "%m/%d/%Y %H:%M:%S").astimezone()
        data: dict[str, str | float] = {}
        data["d"] = timestamp.strftime("%Y%m%d")  # date
        data["t"] = timestamp.strftime("%H:%M")  # time
        data["v2"] = self.getPVFlow()  # PV Generation

        load_flow = self.getLoadFlow()
        if isinstance(load_flow, list):
            data["v4"] = load_flow[0]  # power consumption
        else:
            data["v4"] = load_flow
        temp = self.get_inverter_temperature()
        if isinstance(temp, list):
            data["v5"] = temp[0]  # inverter temperature
        else:
            data["v5"] = temp

        voltage = self.getVoltage()
        if isinstance(voltage, list):
            data["v6"] = voltage[0]
        else:
            data["v6"] = voltage
        return data


class SingleInverter(API):
    """API implementation for an account with a single inverter"""

    def __init__(
        self,
        system_id: str,
        account: str,
        password: str,
        api_url: str = API_URL,
        log_level: str | None = None,
        user_agent: str = DEFAULT_UA,
        skipload: bool = False,
    ) -> None:
        self.loadflow = 0.0
        self.loadflow_direction = ""

        self.data: dict[str, Any]

        # instantiate the base class
        super().__init__(system_id, account, password, api_url, log_level, user_agent, skipload)

    def loaddata(self, filename: str) -> None:
        """loads the ata from a given file"""
        self._loaddata(filename)
        if self.data.get("inverter"):
            self.data["inverter"] = self.data["inverter"][0]

    def get_current_readings(
        self,
        raw: bool = True,
        retry: int = 1,
        maxretries: int = 5,
        delay: int = 30,
    ) -> Any:
        """grabs the data and makes sure self.data only has a single inverter"""

        # update the data
        super().get_current_readings(raw=raw, retry=retry, maxretries=maxretries, delay=delay)

        # reduce self.data['inverter'] to a single dict from a list
        if len(self.data.get("inverter", [])) == 0:
            self.logger.debug("No inverter data found in %s", json.dumps(self.data))
            raise ValueError("No inverter data found")
        self.data["inverter"] = self.data["inverter"][0]

        return self.data

    getCurrentReadings = get_current_readings

    def _get_station_location(self) -> dict[str, str | int]:
        """gets the identified lat and long from the station data"""
        return self.get_station_location()

    def get_station_location(self) -> dict[str, str | int]:
        """gets the identified lat and long from the station data"""
        if not self.data:
            self.getCurrentReadings()
        return {
            "latitude": self.data.get("info", {}).get("latitude"),
            "longitude": self.data.get("info", {}).get("longitude"),
        }

    def getPVFlow(self) -> float:
        """returns the current flow amount of the PV panels"""
        if not self.data:
            self.getCurrentReadings()
        if self.data["powerflow"]["pv"].endswith("(W)"):
            pvflow = self.data["powerflow"]["pv"][:-3]
        else:
            pvflow = self.data["powerflow"]["pv"]
        return float(pvflow)

    def getVoltage(self) -> float:
        """gets the current line voltage"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data["inverter"]["invert_full"]["vac1"])

    def get_day_income(self) -> float:
        """gets the current daily income"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data["kpi"]["day_income"])

    def get_total_income(self) -> float:
        """gets the total income"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data["kpi"]["total_income"])

    def get_total_power(self) -> float:
        """gets the total power generated"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data["kpi"]["total_power"])

    def get_day_power(self) -> float:
        """gets the total power generated"""
        if not self.data:
            self.getCurrentReadings()
        return float(self.data["kpi"]["power"])

    def getLoadFlow(self) -> float:
        if not self.data:
            self.getCurrentReadings()
        load = self.data["powerflow"]["load"]
        loadflow = float(load.removesuffix("(W)"))
        # I'd love to see the *house* generate power
        if self.data["powerflow"].get("loadStatus") == -1:
            loadflow_direction = "Importing"
        elif self.data["powerflow"].get("loadStatus") == 1:
            loadflow_direction = "Using Battery"
        elif "loadStatus" not in self.data["powerflow"]:
            loadflow_direction = "Unknown"
        else:
            raise ValueError(f"Your 'load' is doing something odd - status is '{self.data['powerflow']['loadStatus']}''.")
        self.loadflow = loadflow
        self.loadflow_direction = loadflow_direction
        return loadflow

    def _get_batteries_soc(self) -> float:
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

    def get_inverter_temperature(self) -> float:
        if not self.data:
            self.get_current_readings(True)
        return float(self.data["inverter"]["tempperature"])

    def getDataPvoutput(
        self,
    ) -> dict[str, str | float]:
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
        timestamp = datetime.strptime(self.data.get("info", {}).get("time"), "%m/%d/%Y %H:%M:%S").astimezone()
        data: dict[str, str | float] = {}
        data["d"] = timestamp.strftime("%Y%m%d")  # date
        data["t"] = timestamp.strftime("%H:%M")  # time
        data["v2"] = self.getPVFlow()  # PV Generation
        data["v4"] = self.getLoadFlow()  # power consumption
        data["v5"] = self.get_inverter_temperature()  # inverter temperature
        data["v6"] = self.getVoltage()  # voltage
        return data
