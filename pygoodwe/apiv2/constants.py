"""Region and URL constants for the GoodWe SEMS Plus async client."""

from __future__ import annotations

DEFAULT_TIMEOUT: float = 10.0

SEMSPLUS_REGIONS: dict[str, str] = {
    "cn": "https://cn-semsplus.goodwe.com",
    "eu": "https://eu-semsplus.goodwe.com",
    "au": "https://au-semsplus.goodwe.com",
    "hk": "https://hk-semsplus.goodwe.com",
    "us": "https://us-semsplus.goodwe.com",
}

DEFAULT_REGION: str = "au"

AUTH_LOGIN_PATH = "/web/sems/sems-user/api/v1/auth/cross-login"
AUTH_DEFAULT_SERVICE_PATH = "/web/sems/sems-user/api/v1/auth/default-service"
AUTH_REMOVE_TOKEN_PATH = "/web/sems/sems-user/api/v1/auth/remove-token"

STATIONS_CURRENT_READINGS_PATH = "/web/sems/sems-plant/api/v1/stations/{station_id}/realtime"
STATIONS_LIST_PATH = "/web/sems/sems-plant/api/v1/stations/page"
STATION_BASIC_INFO_PATH = "/web/sems/sems-plant/api/v1/stations/basic/info"
STATION_FLOW_PATH = "/web/sems/sems-plant/api/v1/stations/{station_id}/flow"
STATION_STATISTICS_PATH = "/web/sems/sems-plant/api/v1/stations/{station_id}/statistics"
STATION_PRODUCTION_PATH = "/web/sems/sems-plant/api/v1/stations/{station_id}/production"
STATION_TOPO_PATH = "/web/sems/sems-plant/api/v1/stations/{station_id}/topo"
STATIONS_NO_PLANT_PATH = "/web/sems/sems-plant/api/v1/stations/no-plant"
STATION_ELEC_SOURCE_SETTING_PATH = "/web/sems/sems-plant/api/v1/stations/{station_id}/elecSourceSetting"
STATIONS_AREA_CODE_PATH = "/web/sems/sems-plant/api/v1/stations/area-code"
STATIONS_TIMEZONE_PATH = "/web/sems/sems-plant/api/v1/stations/timezone"
STATIONS_COUNT_PATH = "/web/sems/sems-plant/api/v1/stations/count"

REPORT_EXPORT_DAY_PATH = "/web/sems/sems-report/api/v1/export/day"
REPORT_FILE_PATH_PATH = "/web/sems/sems-report/api/v1/file/path"
REPORT_POWER_REPORT_BY_MONTH_PATH = "/web/sems/sems-report/api/v1/report/month"

PLANT_REVENUE_OVERVIEW_PATH = "/web/sems/sems-plant/api/v1/hems/revenue/overview"
PLANT_REVENUE_CURVE_PATH = "/web/sems/sems-plant/api/v1/hems/revenue/curve"
PLANT_REVENUE_CALENDAR_PATH = "/web/sems/sems-plant/api/v1/hems/revenue/calendar"
PLANT_REVENUE_TOTAL_PATH = "/web/sems/sems-plant/api/v1/hems/revenue/total"
PLANT_POWER_STATISTICS_PATH = "/web/sems/sems-plant/api/v1/hems/power/statisticsAndPreV2"
PLANT_BASIC_PATH = "/web/sems/sems-plant/api/v1/hems/plant/basic"

EV_CHARGE_LOG_PATH = "/web/sems/sems-ev/api/v1/charge-log"
EV_CONFIG_PATH = "/web/sems/sems-ev/api/v1/config"
EV_START_CHARGE_PATH = "/web/sems/sems-ev/api/v1/charge/start"
EV_STOP_CHARGE_PATH = "/web/sems/sems-ev/api/v1/charge/stop"
EV_SCHEDULED_CHARGE_PATH = "/web/sems/sems-ev/api/v1/charge/scheduled"

DEVICE_GET_USERS_BY_SN_PATH = "/web/sems/sems-plant/api/v1/device/get-users-by-sn"

MQTT_URLS: dict[str, str] = {
    "cn": "wss://netty-wss-hz.iot.goodwe-power.com:8885/mqtt",
    "eu": "wss://netty-wss-eu.iot.goodwe-power.com:8885/mqtt",
    "au": "wss://netty-wss-au.iot.goodwe-power.com:8885/mqtt",
    "hk": "wss://netty-wss-hk.iot.goodwe-power.com:8885/mqtt",
    "us": "wss://netty-wss-us.iot.goodwe-power.com:8885/mqtt",
}
