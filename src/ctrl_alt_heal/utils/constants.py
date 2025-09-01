"""Constants used throughout the Ctrl-Alt-Heal application."""

# Session Management
SESSION_TIMEOUT_MINUTES = 15  # Inactivity-based timeout

# History Management
HISTORY_MAX_MESSAGES = 50  # Maximum messages to keep in context
HISTORY_MAX_TOKENS = 8000  # Estimated token limit for history (conservative)
HISTORY_SUMMARY_THRESHOLD = 30  # Start summarizing when messages exceed this
HISTORY_KEEP_RECENT_MESSAGES = 10  # Always keep the most recent N messages
HISTORY_SUMMARY_MAX_LENGTH = 1000  # Maximum length of history summary

# Default Values
DEFAULT_MEDICATION_DURATION_DAYS = 30
DEFAULT_REMINDER_MINUTES = 15
DEFAULT_MEDICATION_TIMES = ["08:00"]  # Default to morning

# Time Formats
TIME_FORMAT_24H = "%H:%M"
TIME_FORMAT_12H_PATTERN = r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)"

# Timezone Mappings (comprehensive)
TIMEZONE_MAPPINGS = {
    # US Timezones (lowercase)
    "est": "America/New_York",
    "eastern": "America/New_York",
    "et": "America/New_York",
    "cst": "America/Chicago",
    "central": "America/Chicago",
    "ct": "America/Chicago",
    "mst": "America/Denver",
    "mountain": "America/Denver",
    "mt": "America/Denver",
    "pst": "America/Los_Angeles",
    "pacific": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    # US Timezones (uppercase)
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "AKST": "America/Anchorage",
    "AKDT": "America/Anchorage",
    "HST": "Pacific/Honolulu",
    "HDT": "Pacific/Honolulu",
    # International (lowercase)
    "gmt": "Europe/London",
    "utc": "UTC",
    "bst": "Europe/London",  # British Summer Time
    "cet": "Europe/Paris",  # Central European Time
    "eet": "Europe/Kiev",  # Eastern European Time
    "jst": "Asia/Tokyo",  # Japan Standard Time
    "aest": "Australia/Sydney",  # Australian Eastern Standard Time
    "ist": "Asia/Kolkata",  # India Standard Time
    "cst_china": "Asia/Shanghai",  # China Standard Time
    "sgt": "Asia/Singapore",  # Singapore Time
    # International (uppercase)
    "UTC": "UTC",
    "GMT": "UTC",
    "SGT": "Asia/Singapore",
    "JST": "Asia/Tokyo",
    "IST": "Asia/Kolkata",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "NZST": "Pacific/Auckland",
    "NZDT": "Pacific/Auckland",
    # Common Names
    "Pacific Time": "America/Los_Angeles",
    "Eastern Time": "America/New_York",
    "Central Time": "America/Chicago",
    "Mountain Time": "America/Denver",
    "Alaska Time": "America/Anchorage",
    "Hawaii Time": "Pacific/Honolulu",
    # Cities (lowercase)
    "new york": "America/New_York",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "singapore": "Asia/Singapore",
    "hong kong": "Asia/Hong_Kong",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    # Cities (proper case)
    "New York": "America/New_York",
    "Los Angeles": "America/Los_Angeles",
    "Chicago": "America/Chicago",
    "Denver": "America/Denver",
    "Seattle": "America/Los_Angeles",
    "Boston": "America/New_York",
    "Miami": "America/New_York",
    "Houston": "America/Chicago",
    "Phoenix": "America/Denver",
    "San Francisco": "America/Los_Angeles",
    "London": "Europe/London",
    "Paris": "Europe/Paris",
    "Berlin": "Europe/Berlin",
    "Madrid": "Europe/Madrid",
    "Rome": "Europe/Rome",
    "Amsterdam": "Europe/Amsterdam",
    "Stockholm": "Europe/Stockholm",
    "Moscow": "Europe/Moscow",
    "Tokyo": "Asia/Tokyo",
    "Seoul": "Asia/Seoul",
    "Beijing": "Asia/Shanghai",
    "Shanghai": "Asia/Shanghai",
    "Hong Kong": "Asia/Hong_Kong",
    "Singapore": "Asia/Singapore",
    "Bangkok": "Asia/Bangkok",
    "Jakarta": "Asia/Jakarta",
    "Manila": "Asia/Manila",
    "Sydney": "Australia/Sydney",
    "Melbourne": "Australia/Melbourne",
    "Auckland": "Pacific/Auckland",
    "Mumbai": "Asia/Kolkata",
    "Delhi": "Asia/Kolkata",
    "Dubai": "Asia/Dubai",
    "Riyadh": "Asia/Riyadh",
    "Cairo": "Africa/Cairo",
    "Johannesburg": "Africa/Johannesburg",
    "Lagos": "Africa/Lagos",
    "Nairobi": "Africa/Nairobi",
    "São Paulo": "America/Sao_Paulo",
    "Buenos Aires": "America/Argentina/Buenos_Aires",
    "Mexico City": "America/Mexico_City",
    "Toronto": "America/Toronto",
    "Vancouver": "America/Vancouver",
    "Montreal": "America/Montreal",
}

# Frequency to Time Mappings
FREQUENCY_TIME_MAPPINGS = {
    "morning": ["08:00"],
    "evening": ["20:00"],
    "night": ["20:00"],
    "afternoon": ["12:00"],
    "noon": ["12:00"],
    "twice": ["08:00", "20:00"],
    "thrice": ["08:00", "14:00", "20:00"],
    "three": ["08:00", "14:00", "20:00"],
    "four": ["08:00", "12:00", "16:00", "20:00"],
}


# Language to Timezone Mappings
LANGUAGE_TIMEZONE_MAPPINGS = {
    "en-US": "America/New_York",
    "en-GB": "Europe/London",
    "en-CA": "America/Toronto",
    "en-AU": "Australia/Sydney",
    "en-NZ": "Pacific/Auckland",
    "en-IN": "Asia/Kolkata",
    "en-SG": "Asia/Singapore",
    "en-MY": "Asia/Kuala_Lumpur",
    "en-PH": "Asia/Manila",
    "en-HK": "Asia/Hong_Kong",
    "en-ZA": "Africa/Johannesburg",
    "en-IE": "Europe/Dublin",
    "en-JM": "America/Jamaica",
    "en-BB": "America/Barbados",
    "en-TT": "America/Port_of_Spain",
    "en-GY": "America/Guyana",
    "en-BZ": "America/Belize",
    "en-BW": "Africa/Gaborone",
    "en-KE": "Africa/Nairobi",
    "en-NG": "Africa/Lagos",
    "en-GH": "Africa/Accra",
    "en-UG": "Africa/Kampala",
    "en-TZ": "Africa/Dar_es_Salaam",
    "en-ZW": "Africa/Harare",
    "en-ZM": "Africa/Lusaka",
    "en-MW": "Africa/Blantyre",
    "en-SZ": "Africa/Mbabane",
    "en-LS": "Africa/Maseru",
    "en-NA": "Africa/Windhoek",
    "en-MU": "Indian/Mauritius",
    "en-SC": "Indian/Mahe",
    "en-MV": "Indian/Maldives",
    "en-LK": "Asia/Colombo",
    "en-BD": "Asia/Dhaka",
    "en-PK": "Asia/Karachi",
    "en-AF": "Asia/Kabul",
    "en-NP": "Asia/Kathmandu",
    "en-BT": "Asia/Thimphu",
    "en-MM": "Asia/Yangon",
    "en-KH": "Asia/Phnom_Penh",
    "en-LA": "Asia/Vientiane",
    "en-VN": "Asia/Ho_Chi_Minh",
    "en-ID": "Asia/Jakarta",
    "en-TH": "Asia/Bangkok",
    # "en-MY": "Asia/Kuala_Lumpur",  # Duplicate key, already defined above
    "en-BN": "Asia/Brunei",
    "en-TL": "Asia/Dili",
    "en-PG": "Pacific/Port_Moresby",
    "en-FJ": "Pacific/Fiji",
    "en-SB": "Pacific/Guadalcanal",
    "en-VU": "Pacific/Efate",
    "en-NC": "Pacific/Noumea",
    "en-PF": "Pacific/Tahiti",
    "en-WS": "Pacific/Apia",
    "en-TO": "Pacific/Tongatapu",
    "en-CK": "Pacific/Rarotonga",
    "en-NU": "Pacific/Niue",
    "en-TK": "Pacific/Fakaofo",
    "en-TV": "Pacific/Funafuti",
    "en-KI": "Pacific/Tarawa",
    "en-NR": "Pacific/Nauru",
    "en-MH": "Pacific/Majuro",
    "en-FM": "Pacific/Pohnpei",
    "en-PW": "Pacific/Palau",
    "en-GU": "Pacific/Guam",
    "en-MP": "Pacific/Saipan",
    "en-AS": "Pacific/Pago_Pago",
    "zh-CN": "Asia/Shanghai",
    "zh-TW": "Asia/Taipei",
    "zh-HK": "Asia/Hong_Kong",
    "zh-SG": "Asia/Singapore",
    "ja-JP": "Asia/Tokyo",
    "ko-KR": "Asia/Seoul",
    "th-TH": "Asia/Bangkok",
    "vi-VN": "Asia/Ho_Chi_Minh",
    "id-ID": "Asia/Jakarta",
    "ms-MY": "Asia/Kuala_Lumpur",
    "ms-SG": "Asia/Singapore",
    "ms-BN": "Asia/Brunei",
    "tl-PH": "Asia/Manila",
    "hi-IN": "Asia/Kolkata",
    "bn-IN": "Asia/Kolkata",
    "ta-IN": "Asia/Kolkata",
    "te-IN": "Asia/Kolkata",
    "mr-IN": "Asia/Kolkata",
    "gu-IN": "Asia/Kolkata",
    "kn-IN": "Asia/Kolkata",
    "ml-IN": "Asia/Kolkata",
    "pa-IN": "Asia/Kolkata",
    "or-IN": "Asia/Kolkata",
    "as-IN": "Asia/Kolkata",
    "ne-NP": "Asia/Kathmandu",
    "my-MM": "Asia/Yangon",
    "km-KH": "Asia/Phnom_Penh",
    "lo-LA": "Asia/Vientiane",
    "si-LK": "Asia/Colombo",
    "bn-BD": "Asia/Dhaka",
    "ur-PK": "Asia/Karachi",
    "ps-AF": "Asia/Kabul",
    "dz-BT": "Asia/Thimphu",
    "de-DE": "Europe/Berlin",
    "de-AT": "Europe/Vienna",
    "de-CH": "Europe/Zurich",
    "de-LU": "Europe/Luxembourg",
    "de-LI": "Europe/Vaduz",
    "fr-FR": "Europe/Paris",
    "fr-CA": "America/Montreal",
    "fr-BE": "Europe/Brussels",
    "fr-CH": "Europe/Zurich",
    "fr-LU": "Europe/Luxembourg",
    "fr-MC": "Europe/Monaco",
    "es-ES": "Europe/Madrid",
    "es-MX": "America/Mexico_City",
    "es-AR": "America/Argentina/Buenos_Aires",
    "es-CO": "America/Bogota",
    "es-PE": "America/Lima",
    "es-VE": "America/Caracas",
    "es-CL": "America/Santiago",
    "es-EC": "America/Guayaquil",
    "es-GT": "America/Guatemala",
    "es-CU": "America/Havana",
    "es-BO": "America/La_Paz",
    "es-DO": "America/Santo_Domingo",
    "es-HN": "America/Tegucigalpa",
    "es-PY": "America/Asuncion",
    "es-SV": "America/El_Salvador",
    "es-NI": "America/Managua",
    "es-PA": "America/Panama",
    "es-PR": "America/Puerto_Rico",
    "es-UY": "America/Montevideo",
    "es-CR": "America/Costa_Rica",
    "pt-BR": "America/Sao_Paulo",
    "pt-PT": "Europe/Lisbon",
    "pt-AO": "Africa/Luanda",
    "pt-MZ": "Africa/Maputo",
    "pt-GW": "Africa/Bissau",
    "pt-CV": "Atlantic/Cape_Verde",
    "pt-ST": "Africa/Sao_Tome",
    "pt-TL": "Asia/Dili",
    "pt-MO": "Asia/Macau",
    "it-IT": "Europe/Rome",
    "it-CH": "Europe/Zurich",
    "it-SM": "Europe/San_Marino",
    "it-VA": "Europe/Vatican",
    "nl-NL": "Europe/Amsterdam",
    "nl-BE": "Europe/Brussels",
    "nl-SR": "America/Paramaribo",
    "nl-CW": "America/Curacao",
    "nl-SX": "America/Lower_Princes",
    "nl-AW": "America/Aruba",
    "nl-BQ": "America/Kralendijk",
    "sv-SE": "Europe/Stockholm",
    "da-DK": "Europe/Copenhagen",
    "no-NO": "Europe/Oslo",
    "fi-FI": "Europe/Helsinki",
    "is-IS": "Atlantic/Reykjavik",
    "fo-FO": "Atlantic/Faroe",
    "pl-PL": "Europe/Warsaw",
    "cs-CZ": "Europe/Prague",
    "sk-SK": "Europe/Bratislava",
    "hu-HU": "Europe/Budapest",
    "ro-RO": "Europe/Bucharest",
    "bg-BG": "Europe/Sofia",
    "hr-HR": "Europe/Zagreb",
    "sl-SI": "Europe/Ljubljana",
    "et-EE": "Europe/Tallinn",
    "lv-LV": "Europe/Riga",
    "lt-LT": "Europe/Vilnius",
    "mt-MT": "Europe/Malta",
    "cy-GB": "Europe/London",
    "ga-IE": "Europe/Dublin",
    "gd-GB": "Europe/London",
    "kw-GB": "Europe/London",
    "ru-RU": "Europe/Moscow",
    "ru-BY": "Europe/Minsk",
    "ru-KZ": "Asia/Almaty",
    "ru-KG": "Asia/Bishkek",
    "ru-TJ": "Asia/Dushanbe",
    "ru-TM": "Asia/Ashgabat",
    "ru-UZ": "Asia/Tashkent",
    "ru-MD": "Europe/Chisinau",
    "ru-AM": "Asia/Yerevan",
    "ru-AZ": "Asia/Baku",
    "ru-GE": "Asia/Tbilisi",
    "uk-UA": "Europe/Kiev",
    "be-BY": "Europe/Minsk",
    "kk-KZ": "Asia/Almaty",
    "ky-KG": "Asia/Bishkek",
    "tg-TJ": "Asia/Dushanbe",
    "tk-TM": "Asia/Ashgabat",
    "uz-UZ": "Asia/Tashkent",
    "ro-MD": "Europe/Chisinau",
    "hy-AM": "Asia/Yerevan",
    "az-AZ": "Asia/Baku",
    "ka-GE": "Asia/Tbilisi",
    "tr-TR": "Europe/Istanbul",
    "tr-CY": "Asia/Nicosia",
    "ar-SA": "Asia/Riyadh",
    "ar-EG": "Africa/Cairo",
    "ar-DZ": "Africa/Algiers",
    "ar-MA": "Africa/Casablanca",
    "ar-TN": "Africa/Tunis",
    "ar-LY": "Africa/Tripoli",
    "ar-SD": "Africa/Khartoum",
    "ar-ER": "Africa/Asmara",
    "ar-DJ": "Africa/Djibouti",
    "ar-SO": "Africa/Mogadishu",
    "ar-KE": "Africa/Nairobi",
    "ar-TZ": "Africa/Dar_es_Salaam",
    "ar-UG": "Africa/Kampala",
    "ar-BI": "Africa/Bujumbura",
    "ar-RW": "Africa/Kigali",
    "ar-CD": "Africa/Kinshasa",
    "ar-CG": "Africa/Brazzaville",
    "ar-CF": "Africa/Bangui",
    "ar-TD": "Africa/Ndjamena",
    "ar-CM": "Africa/Douala",
    "ar-GQ": "Africa/Malabo",
    "ar-GA": "Africa/Libreville",
    "ar-CV": "Atlantic/Cape_Verde",
    "ar-GM": "Africa/Banjul",
    "ar-GN": "Africa/Conakry",
    "ar-GW": "Africa/Bissau",
    "ar-SL": "Africa/Freetown",
    "ar-LR": "Africa/Monrovia",
    "ar-CI": "Africa/Abidjan",
    "ar-BF": "Africa/Ouagadougou",
    "ar-ML": "Africa/Bamako",
    "ar-NE": "Africa/Niamey",
    "ar-TG": "Africa/Lome",
    "ar-BJ": "Africa/Porto-Novo",
    "ar-NG": "Africa/Lagos",
    "ar-GH": "Africa/Accra",
    # "ar-CM": "Africa/Douala",  # Duplicate key, already defined above
    # "ar-GQ": "Africa/Malabo",  # Duplicate key, already defined above
    # "ar-GA": "Africa/Libreville",  # Duplicate key, already defined above
    # "ar-CG": "Africa/Brazzaville",  # Duplicate key, already defined above
    # "ar-CD": "Africa/Kinshasa",  # Duplicate key, already defined above
    "ar-AO": "Africa/Luanda",
    "ar-ZA": "Africa/Johannesburg",
    "ar-NA": "Africa/Windhoek",
    "ar-BW": "Africa/Gaborone",
    "ar-ZW": "Africa/Harare",
    "ar-ZM": "Africa/Lusaka",
    "ar-MW": "Africa/Blantyre",
    "ar-MZ": "Africa/Maputo",
    "ar-SZ": "Africa/Mbabane",
    "ar-LS": "Africa/Maseru",
    "ar-MG": "Indian/Antananarivo",
    "ar-MU": "Indian/Mauritius",
    "ar-SC": "Indian/Mahe",
    "ar-KM": "Indian/Comoro",
    "ar-YT": "Indian/Mayotte",
    "ar-RE": "Indian/Reunion",
    "ar-IO": "Indian/Chagos",
    "ar-MV": "Indian/Maldives",
    "ar-LK": "Asia/Colombo",
    "ar-IN": "Asia/Kolkata",
    "ar-BD": "Asia/Dhaka",
    "ar-MM": "Asia/Yangon",
    "ar-TH": "Asia/Bangkok",
    "ar-KH": "Asia/Phnom_Penh",
    "ar-VN": "Asia/Ho_Chi_Minh",
    "ar-LA": "Asia/Vientiane",
    "ar-MY": "Asia/Kuala_Lumpur",
    "ar-SG": "Asia/Singapore",
    "ar-ID": "Asia/Jakarta",
    "ar-PH": "Asia/Manila",
    "ar-BN": "Asia/Brunei",
    "ar-TL": "Asia/Dili",
    "ar-PG": "Pacific/Port_Moresby",
    "ar-FJ": "Pacific/Fiji",
    "ar-SB": "Pacific/Guadalcanal",
    "ar-VU": "Pacific/Efate",
    "ar-NC": "Pacific/Noumea",
    "ar-PF": "Pacific/Tahiti",
    "ar-WS": "Pacific/Apia",
    "ar-TO": "Pacific/Tongatapu",
    "ar-CK": "Pacific/Rarotonga",
    "ar-NU": "Pacific/Niue",
    "ar-TK": "Pacific/Fakaofo",
    "ar-TV": "Pacific/Funafuti",
    "ar-KI": "Pacific/Tarawa",
    "ar-NR": "Pacific/Nauru",
    "ar-MH": "Pacific/Majuro",
    "ar-FM": "Pacific/Pohnpei",
    "ar-PW": "Pacific/Palau",
    "ar-GU": "Pacific/Guam",
    "ar-MP": "Pacific/Saipan",
    "ar-AS": "Pacific/Pago_Pago",
}

# Error Messages
ERROR_MESSAGES = {
    "USER_NOT_FOUND": "User not found.",
    "MEDICATION_NOT_FOUND": "Medication not found in your prescriptions.",
    "NO_PRESCRIPTIONS": "No prescriptions found for this user.",
    "INVALID_TIME_FORMAT": "Please provide times in a valid format. Examples: ['10am', '2pm', '8pm'] or ['10:00', '14:00', '20:00']",
    "NEEDS_TIMEZONE": "I need to know your timezone first. Could you tell me your timezone? (e.g., 'EST', 'Pacific Time', 'UTC+5')",
    "INVALID_TIMEZONE": "Invalid timezone format. Please provide a valid timezone (e.g., 'EST', 'Pacific Time', 'UTC+5')",
    "SCHEDULE_CREATION_FAILED": "Failed to create medication schedule.",
    "SCHEDULE_UPDATE_FAILED": "Failed to update medication schedule.",
    "SCHEDULE_DELETION_FAILED": "Failed to delete medication schedule.",
    "PRESCRIPTION_EXTRACTION_FAILED": "Failed to extract prescription from image.",
    "IMAGE_PROCESSING_FAILED": "Failed to process image.",
    "FILE_DOWNLOAD_FAILED": "Sorry, I had trouble downloading the image. Please try again.",
    "TELEGRAM_API_ERROR": "Error communicating with Telegram API.",
    "AWS_SERVICE_ERROR": "Error accessing AWS service.",
    "DATABASE_ERROR": "Database operation failed.",
    "VALIDATION_ERROR": "Invalid input data provided.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "SCHEDULE_CREATED": "Medication schedule created successfully.",
    "SCHEDULE_UPDATED": "Medication schedule updated successfully.",
    "SCHEDULE_DELETED": "Medication schedule deleted successfully.",
    "PRESCRIPTION_EXTRACTED": "Prescription extracted successfully.",
    "TIMEZONE_SET": "Timezone set successfully.",
    "USER_CREATED": "User created successfully.",
    "USER_UPDATED": "User updated successfully.",
}

# File Extensions and MIME Types
FILE_EXTENSIONS = {
    "JPEG": [".jpg", ".jpeg"],
    "PNG": [".png"],
    "PDF": [".pdf"],
    "ICS": [".ics"],
}

MIME_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "PDF": "application/pdf",
    "ICS": "text/calendar",
}

# AWS Service Names
AWS_SERVICES = {
    "S3": "s3",
    "DYNAMODB": "dynamodb",
    "SECRETS_MANAGER": "secretsmanager",
    "BEDROCK": "bedrock-runtime",
    # "SQS": "sqs",  # Removed - no longer used with Fargate deployment
}

# DynamoDB Table Names
DYNAMODB_TABLES = {
    "USERS": "USERS_TABLE_NAME",
    "CONVERSATIONS": "CONVERSATIONS_TABLE_NAME",
    "IDENTITIES": "IDENTITIES_TABLE_NAME",
    "PRESCRIPTIONS": "PRESCRIPTIONS_TABLE_NAME",
    "FHIR_DATA": "FHIR_DATA_TABLE_NAME",
}

# Environment Variable Names
ENV_VARS = {
    "AWS_REGION": "AWS_REGION",
    "BEDROCK_MODEL_ID": "BEDROCK_MODEL_ID",
    "BEDROCK_MULTIMODAL_MODEL_ID": "BEDROCK_MULTIMODAL_MODEL_ID",
    "TELEGRAM_SECRET_NAME": "TELEGRAM_SECRET_NAME",
    "SERPER_API_KEY": "SERPER_API_KEY",
    "UPLOADS_BUCKET_NAME": "UPLOADS_BUCKET_NAME",
    # "MESSAGES_QUEUE_URL": "MESSAGES_QUEUE_URL",  # Removed - no longer used with Fargate deployment
}

# Telegram API Constants
TELEGRAM_API = {
    "BASE_URL": "https://api.telegram.org/bot",
    "SEND_MESSAGE_ENDPOINT": "/sendMessage",
    "SEND_FILE_ENDPOINT": "/sendDocument",
    "GET_FILE_ENDPOINT": "/getFile",
    "GET_FILE_PATH_ENDPOINT": "/getFile",
    "TIMEOUT": 30.0,
    "MAX_MESSAGE_LENGTH": 4096,
    "MAX_CAPTION_LENGTH": 1024,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 1.0,  # seconds
    "RATE_LIMIT_DELAY": 0.1,  # seconds between requests
}

# Telegram Message Formatting
TELEGRAM_FORMATTING = {
    "MARKDOWN_V2": "MarkdownV2",
    "HTML": "HTML",
    "MARKDOWN": "Markdown",  # Legacy, deprecated
    "PLAIN_TEXT": "text",
}

# Telegram Message Types
TELEGRAM_MESSAGE_TYPES = {
    "TEXT": "text",
    "DOCUMENT": "document",
    "PHOTO": "photo",
    "VIDEO": "video",
    "AUDIO": "audio",
    "VOICE": "voice",
    "STICKER": "sticker",
    "LOCATION": "location",
    "CONTACT": "contact",
}

# Bedrock Model IDs
BEDROCK_MODELS = {
    "NOVA_LITE": "apac.amazon.nova-lite-v1:0",
    "NOVA": "apac.amazon.nova-1",
    "CLAUDE": "anthropic.claude-3-sonnet-20240229-v1:0",
}

# FHIR Resource Types
FHIR_RESOURCES = {
    "BUNDLE": "Bundle",
    "MEDICATION_REQUEST": "MedicationRequest",
    "PATIENT": "Patient",
    "PRACTITIONER": "Practitioner",
}

# Medication Status Values
MEDICATION_STATUS = {
    "ACTIVE": "active",
    "INACTIVE": "inactive",
    "COMPLETED": "completed",
    "DISCONTINUED": "discontinued",
}

# Response Status Values
RESPONSE_STATUS = {
    "SUCCESS": "success",
    "ERROR": "error",
    "WARNING": "warning",
    "INFO": "info",
}

# Logging Levels
LOG_LEVELS = {
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
}

# HTTP Status Codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}

# Validation Rules
VALIDATION_RULES = {
    "MAX_MEDICATION_NAME_LENGTH": 255,
    "MAX_DOSAGE_LENGTH": 100,
    "MAX_FREQUENCY_LENGTH": 100,
    "MAX_INSTRUCTIONS_LENGTH": 500,
    "MAX_USER_NOTES_LENGTH": 1000,
    "MIN_SCHEDULE_DURATION_DAYS": 1,
    "MAX_SCHEDULE_DURATION_DAYS": 365,
    "MIN_REMINDER_MINUTES": 1,
    "MAX_REMINDER_MINUTES": 1440,  # 24 hours
    "MAX_TIMES_PER_SCHEDULE": 10,
}

# Default Configuration Values
DEFAULT_CONFIG = {
    "DEFAULT_TIMEZONE": "UTC",
    "DEFAULT_LANGUAGE": "en-US",
    "DEFAULT_SESSION_TIMEOUT": 15,
    "DEFAULT_MEDICATION_DURATION": 30,
    "DEFAULT_REMINDER_TIME": 15,
    "DEFAULT_MAX_RETRIES": 3,
    "DEFAULT_TIMEOUT": 30,
}
