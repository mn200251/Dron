from flask import Flask, jsonify, request

app = Flask(__name__)

# motor power percentages -- "in memory db"
motor_pp = {
    "motor1_pp" : 0, "motor2_pp" : 0, "motor3_pp" : 0, "motor4_pp" : 0
}

def get_motor_power_values():
    return jsonify({"motor1_pp": motor_pp["motor1_pp"],
                    "motor2_pp": motor_pp["motor2_pp"],
                    "motor3_pp": motor_pp["motor3_pp"],
                    "motor4_pp": motor_pp["motor4_pp"]})

def log_error_message(error, msg):
    with open("error_log.txt", "a") as f:
        f.write(str(error)); f.write(msg + "|\n")

def set_motor_power_values(
    m1_newv = None, m2_newv = None,
    m3_newv = None, m4_newv = None):
    try:
        if (m1_newv is not None) and (m1_newv < 0 or m1_newv > 1): m1_newv = None
        if (m2_newv is not None) and (m2_newv < 0 or m2_newv > 1): m2_newv = None
        if (m3_newv is not None) and (m3_newv < 0 or m3_newv > 1): m3_newv = None
        if (m4_newv is not None) and (m4_newv < 0 or m4_newv > 1): m4_newv = None
        global motor_pp
        if m1_newv is not None and not m1_newv: motor_pp["motor1_pp"] = 0
        if m2_newv is not None and not m2_newv: motor_pp["motor2_pp"] = 0
        if m3_newv is not None and not m3_newv: motor_pp["motor3_pp"] = 0
        if m4_newv is not None and not m4_newv: motor_pp["motor4_pp"] = 0
        motor_pp["motor1_pp"] = m1_newv or motor_pp["motor1_pp"]
        motor_pp["motor2_pp"] = m2_newv or motor_pp["motor2_pp"]
        motor_pp["motor3_pp"] = m3_newv or motor_pp["motor3_pp"]
        motor_pp["motor4_pp"] = m4_newv or motor_pp["motor4_pp"]
    except Exception as e: log_error_message(e, " in set_motor_power_values")

@app.route("/get_motor_power")
def get_motor_power():
    return get_motor_power_values()

def get_page_content(page):
    page_content = None
    with open(page, "r") as f: page_content = f.read()
    return page_content

@app.route("/set_motor_power_ui", methods=["POST", "GET"])
def set_motor_power_ui():
    if request.method == "GET":
        return get_page_content("set_motor_power_ui_form.html")
    else:
        try:
            nmotor_pp = dict()
            for i in range(1, 5):
                if request.form[f"motor{i}_pp"] != "" and float(request.form[f"motor{i}_pp"]) >= 0.0:
                    nmotor_pp[f"m{i}_newv"] = float(request.form[f"motor{i}_pp"])
            set_motor_power_values(**nmotor_pp)
        except Exception as e: log_error_message(e, " in set_motor_power")
        return get_motor_power_values()

def set_motor_power_api_usage():
    return get_page_content("api_usage_page.html")

@app.route("/set_motor_power_api", methods=["POST", "GET"])
def set_motor_power_api():
    if request.method == "GET": return set_motor_power_api_usage()
    try:
        nmotor_pp = dict()
        for i in range(1, 5):
            if f"motor{i}_pp" in request.json:
                nmotor_pp[f"m{i}_newv"] = request.json[f"motor{i}_pp"]
        set_motor_power_values(**nmotor_pp)
    except Exception as e: log_error_message(e, " in set_motor_power")
    return get_motor_power_values()

if __name__ == "__main__":
    # app.run(debug=True, ssl_context="adhoc") # if you want https
    app.run(debug=True)