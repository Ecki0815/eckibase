import os
import logging
import pymysql
from flask import Flask, request

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

API_KEY_TEMP_AND_HUM = os.environ.get("API_KEY_TEMP_AND_HUM", "3445KLF8SD8")
API_KEY_EVENT = os.environ.get("API_KEY_EVENT", "2398KSFH23J")


def get_conn():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "db"),
        port=int(os.environ.get("DB_PORT", 3306)),
        user=os.environ.get("DB_USER", "db"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "home"),
        connect_timeout=5,
    )


@app.route("/", methods=["GET"])
def index():
    return "No data posted with HTTP POST.", 200


@app.route("/", methods=["POST"])
def handle():
    data = request.get_json(silent=True)
    if not data:
        return "No data posted with HTTP POST.", 400

    api_key = data.get("api_key", "")

    # --- Temperature & Humidity ---
    if api_key == API_KEY_TEMP_AND_HUM:
        required = ["officeTemp", "badTemp", "wcTemp", "szTemp", "wzTemp", "floorTemp",
                    "officeHum",  "badHum",  "wcHum",  "szHum",  "wzHum",  "floorHum"]
        missing = [k for k in required if k not in data]
        if missing:
            return f"Missing fields: {', '.join(missing)}", 400

        try:
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """INSERT INTO TempAndHum
                           (officeTemp, badTemp, wcTemp, szTemp, wzTemp, floorTemp,
                            officeHum,  badHum,  wcHum,  szHum,  wzHum,  floorHum)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        tuple(data[k] for k in required),
                    )
                conn.commit()
            return "New record created successfully", 200
        except Exception as exc:
            logging.error("TempAndHum insert failed: %s", exc)
            return f"Error: {exc}", 500

    # --- Events ---
    elif api_key == API_KEY_EVENT:
        event_type = data.get("type", "")

        try:
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    if event_type == "movement":
                        cur.execute(
                            "INSERT INTO Movement (source, active) VALUES (%s, %s)",
                            (data["source"], data["active"]),
                        )
                    elif event_type == "analog":
                        cur.execute(
                            "INSERT INTO HeatAndBright (source, value) VALUES (%s, %s)",
                            (data["source"], data["value"]),
                        )
                    else:
                        return f"Unknown event type: {event_type}", 400
                conn.commit()
            return "New record created successfully", 200
        except Exception as exc:
            logging.error("Event insert failed: %s", exc)
            return f"Error: {exc}", 500

    else:
        return "Wrong API Key provided.", 403


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
