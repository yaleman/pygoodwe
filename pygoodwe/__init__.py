""" pygoodwe: a (terrible) interface to the goodwe solar API """

import json
import logging
from datetime import datetime
import argparse
import sys
import time
import requests

POWERFLOW_STATUS_TEXT = {
    -1 : "Outward",
}

API_URL = 'https://semsportal.com/api/'

class API():
    """ API implementation """
    def __init__(self, system_id: str, account: str, password: str, **kwargs):
        """
        Options:

        #TODO: lang: Real Soon Now it'll filter out any responses without that language
        skipload: don't run self.getCurrentReadings() on init
        api_url: you can change the API endpoint it hits
        """

        self.system_id = system_id
        self.account = account
        self.password = password
        self.token = '{"version":"v2.0.4","client":"ios","language":"en"}'
        self.global_url = kwargs.get('api_url', API_URL)
        self.base_url = self.global_url

        if kwargs.get('skipload', False):
            logging.debug("Skipping initial load of data")
            self.data = 0
        else:
            logging.debug("Doing load of data")
            self.getCurrentReadings(raw=True)

    def _loaddata(self, filename):
        """ loads a json file of existing data """
        with open(filename, 'r') as filehandle:
            self.data = json.loads(filehandle.read())
        return True

    def loaddata(self, filename):
        """ loads a json object from a file with a string. write this out with json.dumps(self.data) """
        self._loaddata(filename)

    def get_current_readings(self, raw=True, retry=1, maxretries=5, delay=30):
        """ this is an overlay function to help with migration
            to fixing the name of the below function """
        return self.getCurrentReadings(self, raw=raw, retry=retry, maxretries=maxretries, delay=delay) #pylint: disable=redundant-keyword-arg

    def getCurrentReadings(self, raw=True, retry=1, maxretries=5, delay=30): #pylint: disable=invalid-name
        """ gets readings at the current point in time """
        payload = {
            'powerStationId' : self.system_id
        }

        # GOODWE server
        self.data = self.call("v1/PowerStation/GetMonitorDetailByPowerstationId", payload)

        retval = self.data

        if not self.data.get('inverter'):
            if retry < maxretries:
                logging.error('no inverter data, try %s, trying again in %s seconds', retry, delay)
                time.sleep(delay)
                retval = self.getCurrentReadings(raw=raw, retry=retry+1, maxretries=maxretries, delay=delay)
            else:
                logging.error('No inverter data after %s retries, quitting.', retry)
                sys.exit(f"No inverter data after {retry} retries, quitting.")
        return retval

    # def getDayReadings(self, date):
    #     date_s = date.strftime('%Y-%m-%d')
    #     payload = {
    #         'powerStationId' : self.system_id
    #     }
    #     data = self.call("v1/PowerStation/GetMonitorDetailByPowerstationId", payload)
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

    def getDayDetailedReadingsExcel(self, date, **kwargs): #pylint: disable=invalid-name
        """ retrieves the detailed daily results of the given date as an Excel sheet,
            processing the Excel sheet is outside the scope of the current module,
            possible args:
            - filename: the path where to write the output file, default "./Plant_Power_{datestr}.xls
        """
        datestr = datetime.strftime(date, "%Y-%m-%d")
        outputfile = kwargs.get("filename", f"Plant_Power_{datestr}.xls")
        payload = {
            'date' : datestr,
            'pw_id' : self.system_id,
            # since the chart can't be included, use some fixed values that make the sheet look good without it
            'img_width': 350,
            'img_height': 20
            }
        # grab the ID of a file download with the export in it
        download_id = self.call("v1/PowerStation/ExportPowerstationPac", payload)
        if not download_id:
            return False

        payload = {
            'id' : download_id,
        }
        file_data = self.call("v1/ReportData/GetStationPowerDataFilePath", payload)

        if file_data and file_data.get("file_path") is not None:
            try:
                response = requests.get(file_data.get("file_path"), allow_redirects=True)
                response.raise_for_status()
            except Exception as error_message: #pylint: disable=broad-except
                logging.error("Failed to query file download path: %s", error_message)
            try:
                open(outputfile, 'wb').write(response.content)
                return True
            except Exception as error_message: #pylint: disable=broad-except
                logging.error("Failed to write file %s! Error: %s", outputfile, error_message)
                return False
        return False

    def call(self, url: str, payload: str, max_tries: int = 10): #pylint: disable=unused-argument
        """ makes a call to the API """
        for i in range(1, max_tries):
            try:
                headers = {
                    'User-Agent': 'PVMaster/2.0.4 (iPhone; iOS 11.4.1; Scale/2.00)',
                    'Token': self.token,
                    }

                response = requests.post(self.base_url + url, headers=headers, data=payload, timeout=10)
                response.raise_for_status()
                data = response.json()
                logging.debug("call response.json(): %s", json.dumps(data))

                # Some APIs return "success", some "Success" in the 'msg'
                if data.get('msg', "").lower() == 'success' and data.get('data'): #pylint: disable=no-else-return
                    return data.get('data')
                else:
                    login_payload = {
                        'account': self.account,
                        'pwd': self.password,
                        }
                    response = requests.post(self.global_url + 'v1/Common/CrossLogin',
                                             headers=headers,
                                             data=login_payload,
                                             timeout=10,
                                             )
                    response.raise_for_status()
                    data = response.json()
                    self.base_url = data.get('api')
                    self.token = json.dumps(data.get('data'))
            except requests.exceptions.RequestException as exp:
                logging.warning("RequestException: %s", exp)
            time.sleep(i ** 3)

        logging.error("Failed to call GoodWe API")
        return {}

    def parseValue(self, value, unit): #pylint: disable=invalid-name, no-self-use
        """ takes a string value and reutrns it as a float (if possible) """
        try:
            return float(value.rstrip(unit))
        except ValueError as exp:
            logging.warning("ValueError: %s", exp)
            return 0

    def are_batteries_full(self, fullstate: float = 100.0):
        """ boolean result for if the batteries are full. you can set your given 'full'
            percentage in float if you want to lower this a little
            are_batteries_full(fullstate=90.0): returns bool
        """
        for battery in self.get_batteries_soc():
            if battery < fullstate:
                return False
        return True


    def _get_batteries_soc(self):
        """ returns a list of the state of charge for the batteries
        returns: list[float,]
        """
        if not self.data:
            self.getCurrentReadings()
        return [float(inverter.get('invert_full',{}).get('soc')) for inverter in self.data.get('inverter')]

    def get_batteries_soc(self):
        """ return the battery state of charge """
        return self._get_batteries_soc()

    def getPVFlow(self): #pylint: disable=invalid-name
        """ PV flow data """
        raise NotImplementedError("SingleInverter has this, multi does not")

    def getVoltage(self): #pylint: disable=invalid-name
        """ returns the a list of the first AC channel voltages """
        if not self.data:
            self.getCurrentReadings(True)
        return [float(inverter.get('invert_full',{}).get('vac1')) for inverter in self.data.get('inverter')]

    def getPmeter(self): #pylint: disable=invalid-name
        """ gets the current line pmeter """
        if not self.data:
            self.getCurrentReadings()
        return float(self.data.get('inverter',{}).get('invert_full',{}).get('pmeter'))

    def getLoadFlow(self): #pylint: disable=invalid-name
        """ returns the list of inverter multi-unit load watts """
        raise NotImplementedError("multi-unit load watts isn't implemented yet")

    def get_inverter_temperature(self):
        """ returns the list of inverter temperatures """
        if not self.data:
            self.get_current_readings(True)
        return [float(inverter.get('invert_full',{}).get('tempperature')) for inverter in self.data.get('inverter')]

    def getDataPvoutput(self): #pylint: disable=invalid-name
        """ updates and returns the data necessary for a one-shot pvoutput upload
            'd' : testdate.strftime("%Y%m%d"),
            't' : testtime.strftime("%H:%M"),
            'v2' : 500, # power generation
            'v4' : 450,
            'v5' : 23.5, # temperature
            'v6' : 234.0, # voltage
        """
        if not self.data:
            self.getCurrentReadings()
        #"time": "10/04/2019 14:37:29"
        timestamp = datetime.strptime(self.data.get('info',{}).get('time'), '%m/%d/%Y %H:%M:%S')
        data = {}
        data['d'] = timestamp.strftime("%Y%m%d") # date
        data['t'] = timestamp.strftime("%H:%M") # time
        data['v2'] = self.getPVFlow() # PV Generation
        data['v4'] = self.getLoadFlow() # power consumption
        data['v5'] = self.get_inverter_temperature() # inverter temperature
        data['v6'] = self.getVoltage() # voltage
        return data

class SingleInverter(API):
    """ API implementation for an account with a single inverter """
    def __init__(self, system_id: str, account: str, password: str, **kwargs):
        self.loadflow = 0
        self.loadflow_direction = None

        # instantiate the base class
        super().__init__(system_id, account, password, **kwargs)

    def loaddata(self, filename):
        self._loaddata(filename)
        if self.data.get('inverter'):
            self.data['inverter'] = self.data['inverter'][0]

    def getCurrentReadings(self, raw=True, retry=1, maxretries=5, delay=30):
        """ grabs the data and makes sure self.data only has a single inverter """
        # update the data
        super().getCurrentReadings(self, raw)
        # reduce self.data['inverter'] to a single dict from a list
        retval = False
        if self.data.get('inverter'):
            self.data['inverter'] = self.data['inverter'][0]
        else:
            if retry < maxretries:
                logging.error('no inverter data, try %s, trying again in %s seconds', retry, delay)
                time.sleep(delay)
                retval = self.getCurrentReadings(raw=raw, retry=retry+1, maxretries=maxretries, delay=delay)
            else:
                logging.error('No inverter data after %s retries, quitting.', retry)
                sys.exit(f"No inverter data after {retry} retries, quitting.")
        return retval

    def _get_station_location(self):
        """ gets the identified lat and long from the station data """
        return self.get_station_location()

    def get_station_location(self):
        """ gets the identified lat and long from the station data """
        if not self.data:
            self.getCurrentReadings()
        return {
            'latitude' : self.data.get('info',{}).get('latitude'),
            'longitude' : self.data.get('info',{}).get('longitude')
        }

    def getPVFlow(self):
        """ returns the current flow amount of the PV panels """
        if not self.data:
            self.getCurrentReadings()
        if self.data['powerflow']['pv'].endswith('(W)'):
            pvflow = self.data['powerflow']['pv'][:-3]
        else:
            pvflow = self.data['powerflow']['pv']
        return float(pvflow)

    def getVoltage(self):
        """ gets the current line voltage """
        if not self.data:
            self.getCurrentReadings()
        return float(self.data['inverter']['invert_full']['vac1'])

    def getLoadFlow(self):
        if not self.data:
            self.getCurrentReadings()
        if self.data['powerflow']['bettery'].endswith('(W)'):
            loadflow = float(self.data['powerflow']['load'][:-3])
        else:
            loadflow = float(self.data['powerflow']['load'])
        # I'd love to see the *house* generate power
        if self.data['powerflow']['loadStatus'] == -1:
            loadflow_direction = "Importing"
        elif self.data['powerflow']['loadStatus'] == 1:
            loadflow_direction = "Using Battery"
        else:
            raise ValueError(f"Your 'load' is doing something odd - status is '{self.data['powerflow']['loadStatus']}''.") #pylint: disable=line-too-long
        self.loadflow = loadflow
        self.loadflow_direction = loadflow_direction
        return loadflow

    def _get_batteries_soc(self):
        """ returns the state of charge of the battery
        """
        if not self.data:
            self.getCurrentReadings()
        if not self.data.get('soc', False):
            raise ValueError('No state of charge available from data')
        return float(self.data['soc'].get('power'))

    def get_battery_soc(self):
        """ returns the single value state of charge for the batteries in the plant
        returns : float
        """
        return self._get_batteries_soc()

    def get_inverter_temperature(self):
        if not self.data:
            self.get_current_readings(True)
        return float(self.data['inverter']['tempperature'])
