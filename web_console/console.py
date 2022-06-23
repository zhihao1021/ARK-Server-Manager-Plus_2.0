from flask import Flask, render_template, redirect, request, Request, url_for
import logging
from modules.config import Config
from modules.json import Json

logger = logging.getLogger("main")

def deal_requeste(type_of: str, data: str | bytes, raw_requests: Request):
    logger.info(f"Get Request Type:{type_of}")
    try:
        logger.info(f"Data:{data.decode('utf-8')}")
    except:
        logger.info(f"Data:{data}")
    if type_of == "include":
        return render_template(Json.loads(data).get("file_name"))
    return ("", 204)

class Console():
    app = Flask(__name__)
    
    @app.route("/", methods=["GET", "POST"])
    def root():
        request_type = request.headers.get("Request-type")
        if request_type != None:
            return deal_requeste(request_type, request.get_data(), request)
        return redirect(url_for("home"))
    
    @app.route("/home")
    def home():
        return render_template("home.html")
    
    @app.route("/rule")
    def rule():
        return render_template("rule.html")
    
    @app.route("/data")
    def data():
        return render_template("data.html")
    
    def run(self):
        self.app.run(
            host=Config.web_console.host,
            port=Config.web_console.port,
            debug=Config.web_console.debug,
            use_reloader=False
        )