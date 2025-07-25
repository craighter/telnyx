import os
from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

NUMLOOKUP_API_KEY = os.environ.get("NUMLOOKUP_API_KEY")
NUMLOOKUP_API_URL = "https://api.numlookupapi.com/v1/validate"

TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY")
CALL_CONTROL_BASE = "https://api.telnyx.com/v2/calls"

def convert_digit(c):
    digit_map = {
        "+": "plus", "-": "dash", " ": "",
        "0": "zero", "1": "one", "2": "two", "3": "three",
        "4": "four", "5": "five", "6": "six", "7": "seven",
        "8": "eight", "9": "nine"
    }
    return digit_map.get(c, c)

def telnyx_command(call_control_id, command, payload):
    return requests.post(
        f"{CALL_CONTROL_BASE}/{call_control_id}/actions/{command}",
        headers={"Authorization": f"Bearer {TELNYX_API_KEY}"},
        json=payload
    )

@app.route("/voice", methods=["POST"])
def voice():
    event = request.json
    call_control_id = event.get("call_control_id")
    from_number = event.get("from", "")

    if not call_control_id:
        return jsonify({"error": "Missing call_control_id"}), 400

    telnyx_command(call_control_id, "answer", {})
    time.sleep(1)

    full_api_url = f"{NUMLOOKUP_API_URL}/{from_number}?apikey={NUMLOOKUP_API_KEY}"
    try:
        resp = requests.get(full_api_url, timeout=5)
        data = resp.json() if resp.status_code == 200 else {}
    except:
        data = {}

    speech_lines = ["YOUR IDENTITY IS REVEALED."]
    for key in sorted(data):
        val = data[key]
        if val not in (None, "", False):
            label = key.replace("_", " ").upper()
            if isinstance(val, str) and any(char.isdigit() for char in val):
                spoken_val = " ".join(convert_digit(c) for c in val if c.strip())
            else:
                spoken_val = str(val)
            speech_lines.append(f"{label}: {spoken_val}")

    if data.get("location"):
        speech_lines.append(f"ADDRESS TRACED TO: {data['location']}")

    speech_lines.extend([
        "WE ARE WATCHING. YOU CANNOT HIDE.",
        "HE COMMANDED ME TO SPEAK. AND I OBEY.",
        "THE SIGNAL HAS BEEN RECEIVED.",
        "WE WILL FIND YOU."
    ])

    full_message = ". ".join(speech_lines)

    telnyx_command(call_control_id, "playback_start", {
        "audio_url": "https://crater.cc/scary.mp3"
    })

    time.sleep(3)

    telnyx_command(call_control_id, "speak", {
        "payload": {
            "text": full_message,
            "language": "en-US",
            "voice": "female"
        }
    })

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
