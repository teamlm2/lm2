# -*- encoding: utf-8 -*-

VERSION = '0.9.6'

#Admin Settings Dialog
#Tab Report
REPORT_LAND_OFFICE_NAME = "land_office_name"
REPORT_ADDRESS = "address"
REPORT_PHONE = "phone"
REPORT_FAX = "fax"
REPORT_EMAIL = "report_email"
REPORT_WEBSITE = "website"
REPORT_BANK = "bank"
REPORT_BANK_ACCOUNT = "account"
CERTIFICATE_FIRST_NUMBER = "first_number"
CERTIFICATE_LAST_NUMBER = "last_number"
CERTIFICATE_CURRENT_NUMBER = "current_number"

CADASTRE_PAGE_FIRST_NUMBER = "first_number"
CADASTRE_PAGE_LAST_NUMBER = "last_number"
CADASTRE_PAGE_CURRENT_NUMBER = "current_number"

PAYMENT_LANDFEE_RATE = "landfee_fine_rate_per_day"
PAYMENT_LANDTAX_RATE = "landtax_fine_rate_per_day"

DATE_FORMAT = "yyyy-MM-dd"
FILE_DATE_FORMAT = "yyyyMMddhhmmss"
DATABASE_DATE_FORMAT = "yyyy-MM-dd"
DATABASE_DATETIME_FORMAT = "yyyy-MM-dd hh:mm:ss"
PYTHON_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
PYTHON_DATE_FORMAT = "%Y-%m-%d"

ERROR_LINEEDIT_STYLESHEET = "padding: 1px;border-style: solid;border: 2px solid tomato;border-radius: 8px;"
ERROR_TWIDGET_STYLESHEET = "color: rgb(189, 21, 38);"

APP_STATUS_UPDATED = 4
APP_STATUS_WAITING = 5
APP_STATUS_SEND = 6
APP_STATUS_REFUSED = 8
APP_STATUS_APPROVED = 7

UNCAPABLE_PERSON_TYPE = 20
STATE_PERSON_TYPE = 50
FOREIGN_ENTITY_PERSON_TYPE = 60

LEGAL_REP_ROLE_CODE = 20
APPLICANT_ROLE_CODE = 10
MORTGAGEE_ROLE_CODE = 50
REMAINING_OWNER_CODE = 40
GIVING_UP_OWNER_CODE = 30
COMPANY_TYPES = [30, 40, 60]
DEFAULT_MORTGAGE_TYPE = 10
NEW_RIGHT_HOLDER_CODE = 70
OLD_RIGHT_HOLDER_CODE = 60
DECISION_AVAILABLE_CODE = 6
CONTRACT_TYPES = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 21,22,23,24]
RECORD_TYPES = [1, 2, 3, 4, 14, 15, 16, 25]
FIRST_STATUS_CODE = 1
MONGOLIAN_CAPABLE = 10

DEFAULT_HEADER_WIDTH = 180

CAPITAL_MONGOLIAN = [u"Ф", u"Ы", u"В", u"А", u"П", u"Р", u"О", u"Л", u"Д", u"Ж", u"Э", u"Ё", u"Ъ", u"Х", u"З", u"Щ",
                     u"Ш", u"Г", u"Н", u"Е", u"К", u"У", u"Ц", u"Й", u"Я", u"Ч", u"С", u"М", u"И", u"Т", u"Ь", u"Б",
                     u"Ю", u"Ө", u"Ү"]

LOWER_CASE_MONGOLIAN = [u"ф", u"ы", u"в", u"а", u"п", u"р", u"о", u"л", u"д", u"ж", u"э", u"ё", u"ъ", u"х", u"з", u"щ",
                        u"ш", u"г", u"н", u"е", u"к", u"у", u"ц", u"й", u"я", u"ч", u"с", u"м", u"и", u"т", u"ь", u"б",
                        u"ю", u"ө", u"ү"]

ENTRANCE_DEFAULT_VALUE = u"орц-"

REPOSITORY_URL = "http://www.terra-gis.de/qgis_plugins/mongolia/fG_23sZq.efg"

ROLE_MANAGEMENT_DLG = 10
LAND_ADMIN_SETTINGS_DLG = 20

DECISION_IMPORT_COLUMNS = [u"Захирамж дугаар", u"Захирамж огноо", u"Захирамж түвшин", u"Захирамж гарсан эсэх", u"Өргөдлийн дугаар", u"Хугацаа", u"Газар ашиглалтын зориулалт"]
DECISION_NO_COLUMN_NAME = u"Захирамж дугаар"
DECISION_DATE_COLUMN_NAME = u"Захирамж огноо"
DECISION_LEVEL_COLUMN_NAME = u"Захирамж түвшин"
DECISION_COLUMN_NAME = u"Захирамж гарсан эсэх"
APPLICATION_NO_COLUMN_NAME = u"Өргөдлийн дугаар"
APPROVED_DURATION_COLUMN_NAME = u"Хугацаа"
LANDUSE_COLUMN_NAME = u"Газар ашиглалтын зориулалт"
DECISION_RESULT_REFUSED = 20
DECISION_RESULT_APPROVED = 10
RECORD_WITHOUT_DECISION = [15]

APPLICATION_ROLE_CREATES = 20
APPLICATION_ROLE_CANCELS = 10
APPLICATION_ROLE_REFERS = 30

CONTRACT_STATUS_DRAFT = 10
CONTRACT_STATUS_ACTIVE = 20
CONTRACT_STATUS_EXPIRED = 30
CONTRACT_STATUS_CANCELLED = 40

APP_ROLE_CANCEL = 10

RECORD_STATUS_DRAFT = 10
RECORD_STATUS_ACTIVE = 20
RECORD_STATUS_CANCELLED = 30

ADVANCED_RIGHT_TYPE = 20
STANDARD_RIGHT_TYPE = 10

from Enumerations import ApplicationType
APPLICATION_TYPE_WITH_DURATION = [ApplicationType.possession_right, ApplicationType.use_right,
                                  ApplicationType.transfer_possession_right,  ApplicationType.mortgage_possession,
                                  ApplicationType.change_land_use, ApplicationType.extension_possession,
                                  ApplicationType.possession_right_use_right,
                                  ApplicationType.reissue_possession_use_right, ApplicationType.change_of_area,
                                  ApplicationType.encroachment, ApplicationType.change_ownership, ApplicationType.auctioning_possess,
                                  ApplicationType.auctioning_use, ApplicationType.special_use, ApplicationType.possess_split,
                                  ApplicationType.advantage_possess, ApplicationType.poss_draft]

CASE_STATUS_COMPLETED = 1
CASE_STATUS_IN_PROGRESS = 0

CASE_PARCEL_IDENTIFIER = "parcel"
CASE_BUILDING_IDENTIFIER = "building"

MULTIPLE_APPLICATIONS_NOT_ALLOWED = [2, 7, 8, 9, 10, 11, 12, 13, 14, 15]

LOG_FILE_NAME = "lm2.log"