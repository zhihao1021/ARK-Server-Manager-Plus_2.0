from flask import Flask
import logging
import logging.config
from datetime import datetime, time, timezone, timedelta

utc_tz = timezone.utc
tpa_tz = timezone(timedelta(hours=8))
td = timedelta(minutes=1)
target = (datetime.now(utc_tz) + td).timetz()
print(target)

logging.config.dictConfig(
    {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                "format": "[%(asctime)s][%(levelname)s][%(threadName)s]: %(message)s",
            }
        },
        'handlers':
        {
            'custom_handler': {
                'class' : 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'default',
                'level': 'INFO',
                "filename": "logs/latest.log",
                "when": "M",
                "interval": 1,
                "encoding": "utf-8",
                "atTime": target
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['custom_handler']
        },
        "werkzeug": {
            'level': 'INFO',
            'handlers': ['custom_handler']
        }
    }
)

app = Flask("Flask")

@app.route("/")
def root():
    return "Hello World"

app.run("0.0.0.0", 8080)