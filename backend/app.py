import base64
import json
import mimetypes
import os
import smtplib
import threading
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import quote

from flask import Flask, jsonify, make_response, request, send_from_directory
from flask_cors import CORS


# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = ROOT_DIR / "uploads"

SITE_DATA_FILE = DATA_DIR / "site-data.json"
USERS_DATA_FILE = DATA_DIR / "users.json"
ENQUIRIES_DATA_FILE = DATA_DIR / "enquiries.json"
ORDERS_DATA_FILE = DATA_DIR / "orders.json"

# ─── Config ───────────────────────────────────────────────────────────────────

COOKIE_NAME = "adminAuth"
SESSION_MAX_AGE = 12 * 60 * 60  # 12 hours

IMAGE_LIMITS = {
    "admin": 8,
    "agriculture": 6,
    "doors": 6,
    "chogaths": 4,
}

# ─── Defaults ─────────────────────────────────────────────────────────────────

DEFAULT_SITE_DATA = {
    "business": {
        "aboutText": "Momi Repairing Works offers dependable repairing and fabrication work for agriculture machines, main doors and chogaths.",
        "welcomeText": "We provide high quality repairing and manufacturing services for agriculture machines, main doors and chogaths. Our goal is to deliver strong, durable and reliable work with customer satisfaction.",
        "phone": "+91 98765 43210",
        "whatsapp": "+91 98765 43210",
        "address": "Your workshop address, city, state",
        "email": "momiworks@example.com",
        "instagram": "https://www.instagram.com/",
        "facebook": "https://www.facebook.com/",
    },
    "services": {
        "agriculture": {
            "description": "Repairing, welding and maintenance support for agriculture machines that need strong and long-lasting performance.",
            "enabled": True,
        },
        "doors": {
            "description": "Custom-built and repaired main doors made with durable materials, solid fitting and a neat finish.",
            "enabled": True,
        },
        "chogaths": {
            "description": "Strong, custom-sized chogaths created for long life, reliable support and clean installation.",
            "enabled": True,
        },
    },
    "galleries": {
        "admin": [],
        "agriculture": [],
        "doors": [],
        "chogaths": [],
    },
}

DEFAULT_USERS_DATA = {
    "username": "ranjeetsingh",
    "password": "88900838582",
}

DEFAULT_ENQUIRIES = []
DEFAULT_ORDERS = []

# ─── App Setup ────────────────────────────────────────────────────────────────

file_lock = threading.Lock()

app = Flask(__name__)

FRONTEND_URL = os.environ.get("MRW_FRONTEND_URL", "http://localhost:5500")
allowed_origins = [
    FRONTEND_URL,
    r"http://localhost:\d+",
    r"http://127\.0\.0\.1:\d+",
    "http://localhost",
    "http://127.0.0.1",
    "null",
]
CORS(app, supports_credentials=True, origins=allowed_origins)



# ─── Startup ──────────────────────────────────────────────────────────────────

def ensure_project_files():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)

    write_json_if_missing(SITE_DATA_FILE, DEFAULT_SITE_DATA)
    write_json_if_missing(USERS_DATA_FILE, DEFAULT_USERS_DATA)
    write_json_if_missing(ENQUIRIES_DATA_FILE, DEFAULT_ENQUIRIES)
    write_json_if_missing(ORDERS_DATA_FILE, DEFAULT_ORDERS)

    for category in IMAGE_LIMITS:
        (UPLOADS_DIR / category).mkdir(parents=True, exist_ok=True)


# ─── JSON Helpers ─────────────────────────────────────────────────────────────

def write_json_if_missing(path, payload):
    if not path.exists():
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def copy_data(value):
    return json.loads(json.dumps(value))


def load_json(path, fallback):
    try:
        if not path.exists():
            return copy_data(fallback)
        with file_lock:
            data = json.loads(path.read_text(encoding="utf-8"))
        return data
    except (OSError, json.JSONDecodeError):
        return copy_data(fallback)


def save_json(path, payload):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with file_lock:
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def get_json_body():
    data = request.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        return {}
    return data


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ─── Auth Helpers ─────────────────────────────────────────────────────────────

def get_authenticated_username():
    username = request.cookies.get(COOKIE_NAME)
    if not username:
        return None
    users = load_json(USERS_DATA_FILE, DEFAULT_USERS_DATA)
    if username == str(users.get("username", "")):
        return username
    return None


def require_auth():
    username = get_authenticated_username()
    if not username:
        return None, (jsonify({"error": "Unauthorized"}), 401)
    return username, None


# ─── Data Loaders ─────────────────────────────────────────────────────────────

def load_site_data():
    data = load_json(SITE_DATA_FILE, DEFAULT_SITE_DATA)
    if not isinstance(data, dict):
        data = copy_data(DEFAULT_SITE_DATA)

    data.setdefault("business", {})
    data.setdefault("services", {})
    data.setdefault("galleries", {})

    for category in IMAGE_LIMITS:
        data["galleries"].setdefault(category, [])

    return data


def load_enquiries():
    enquiries = load_json(ENQUIRIES_DATA_FILE, DEFAULT_ENQUIRIES)
    return enquiries if isinstance(enquiries, list) else []


def load_orders():
    orders = load_json(ORDERS_DATA_FILE, DEFAULT_ORDERS)
    return orders if isinstance(orders, list) else []


# ─── Validators ───────────────────────────────────────────────────────────────

def validate_required_fields(fields, required):
    cleaned = {}
    for field in required:
        value = str(fields.get(field, "")).strip()
        if not value:
            return None, f"{field} is required"
        cleaned[field] = value
    return cleaned, None


def validate_agriculture_order(fields):
    required = ["machineName", "weight", "color", "comment", "customerName", "phone"]
    return validate_required_fields(fields, required)


def validate_doors_order(fields):
    required = ["doorType", "size", "weight", "color", "customerName", "phone"]
    cleaned, error = validate_required_fields(fields, required)
    if error:
        return None, error
    if cleaned["doorType"] not in {"Main", "Normal"}:
        return None, "Door type must be Main or Normal"
    return cleaned, None


def validate_chogaths_order(fields):
    required = ["sizeOption", "weight", "customerName", "phone"]
    cleaned, error = validate_required_fields(fields, required)
    if error:
        return None, error
    cleaned["customSize"] = str(fields.get("customSize", "")).strip()
    cleaned["companyName"] = str(fields.get("companyName", "")).strip()
    return cleaned, None


# ─── Utility Helpers ──────────────────────────────────────────────────────────

def get_service_label(service):
    labels = {
        "agriculture": "Agricultural Machine",
        "doors": "Main Door",
        "chogaths": "Chogath",
    }
    return labels.get(service, service)


def normalize_phone_number(value):
    return "".join(char for char in str(value) if char.isdigit())


def pretty_label(value):
    mapping = {
        "machineName": "Machine Name",
        "weight": "Weight",
        "color": "Colour",
        "comment": "Comment and Suggestion",
        "customerName": "Customer Name",
        "phone": "Phone",
        "doorType": "Door Type",
        "size": "Size",
        "sizeOption": "Chogath Size",
        "customSize": "Your Size",
        "companyName": "Company Name",
    }
    return mapping.get(value, value)


def build_order_whatsapp_payload(order):
    business = load_site_data().get("business", {})
    whatsapp_number = normalize_phone_number(
        business.get("whatsapp") or business.get("phone") or ""
    )
    if not whatsapp_number:
        return {"number": "", "text": "", "webUrl": ""}

    lines = [f"New Order: {order['label']}"]
    for key, value in order["fields"].items():
        if value:
            lines.append(f"{pretty_label(key)}: {value}")
    lines.append(f"Submitted At: {order['createdAt']}")

    raw_text = "\n".join(lines)
    return {
        "number": whatsapp_number,
        "text": raw_text,
        "webUrl": f"https://wa.me/{whatsapp_number}?text={quote(raw_text)}",
    }


def persist_base64_file(item, category):
    if not isinstance(item, dict):
        return None, "Invalid file payload"

    original_name = str(item.get("name", "image")).strip() or "image"
    data_url = str(item.get("dataUrl", "")).strip()
    if not data_url.startswith("data:image/") or ";base64," not in data_url:
        return None, "Only image data URLs are supported"

    header, encoded = data_url.split(";base64,", 1)
    mime_type = header.removeprefix("data:")
    extension = mimetypes.guess_extension(mime_type) or ".webp"
    filename = f"{uuid.uuid4().hex}{extension}"
    output_path = UPLOADS_DIR / category / filename

    try:
        file_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, base64.binascii.Error):
        return None, "Invalid base64 image data"

    try:
        output_path.write_bytes(file_bytes)
    except OSError:
        return None, "Could not save image"

    return {
        "id": uuid.uuid4().hex,
        "filename": original_name,
        "url": f"/uploads/{category}/{filename}",
        "uploadedAt": now_iso(),
    }, None


def send_enquiry_email(enquiry):
    smtp_host = os.environ.get("MRW_SMTP_HOST", "").strip()
    smtp_port = os.environ.get("MRW_SMTP_PORT", "").strip()
    smtp_username = os.environ.get("MRW_SMTP_USERNAME", "").strip()
    smtp_password = os.environ.get("MRW_SMTP_PASSWORD", "").strip()
    smtp_to = os.environ.get("MRW_NOTIFY_TO", "").strip()
    smtp_from = os.environ.get("MRW_NOTIFY_FROM", smtp_username).strip()

    if not all([smtp_host, smtp_port, smtp_username, smtp_password, smtp_to, smtp_from]):
        return

    try:
        port = int(smtp_port)
    except ValueError:
        return

    message = EmailMessage()
    message["Subject"] = f"New enquiry from {enquiry['name']}"
    message["From"] = smtp_from
    message["To"] = smtp_to
    message.set_content(
        "\n".join(
            [
                "New contact enquiry received.",
                f"Name: {enquiry['name']}",
                f"Phone: {enquiry['phone']}",
                f"Email: {enquiry['email'] or 'Not provided'}",
                f"Service: {enquiry['service']}",
                f"Submitted: {enquiry['createdAt']}",
                "",
                "Message:",
                enquiry["message"],
            ]
        )
    )

    try:
        with smtplib.SMTP(smtp_host, port, timeout=10) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
    except OSError:
        return


# ─── Public Routes ────────────────────────────────────────────────────────────

@app.route("/")
def root():
    return jsonify({"status": "Momi Repairing Works API is running"})


@app.route("/api/public/site-data", methods=["GET"])
def site_data():
    return jsonify(load_site_data())


@app.route("/api/public/enquiries", methods=["POST"])
def create_enquiry():
    payload = get_json_body()
    required_fields = ["name", "phone", "service", "message"]
    enquiry = {}

    for field in required_fields:
        value = str(payload.get(field, "")).strip()
        if not value:
            return jsonify({"error": f"{field} is required"}), 400
        enquiry[field] = value

    enquiry["email"] = str(payload.get("email", "")).strip()
    enquiry["id"] = uuid.uuid4().hex
    enquiry["createdAt"] = now_iso()

    enquiries = load_enquiries()
    enquiries.insert(0, enquiry)
    if not save_json(ENQUIRIES_DATA_FILE, enquiries):
        return jsonify({"error": "Could not save enquiry"}), 500

    send_enquiry_email(enquiry)
    return jsonify({"message": "Enquiry submitted successfully", "enquiry": enquiry}), 201


@app.route("/api/public/orders", methods=["POST"])
def create_order():
    payload = get_json_body()
    service = str(payload.get("service", "")).strip()
    fields = payload.get("fields", {})

    if service not in {"agriculture", "doors", "chogaths"}:
        return jsonify({"error": "Invalid service selected"}), 400
    if not isinstance(fields, dict):
        return jsonify({"error": "Invalid order fields"}), 400

    validators = {
        "agriculture": validate_agriculture_order,
        "doors": validate_doors_order,
        "chogaths": validate_chogaths_order,
    }
    normalized, error = validators[service](fields)
    if error:
        return jsonify({"error": error}), 400

    order = {
        "id": uuid.uuid4().hex,
        "service": service,
        "label": get_service_label(service),
        "fields": normalized,
        "createdAt": now_iso(),
    }

    orders = load_orders()
    orders.insert(0, order)
    if not save_json(ORDERS_DATA_FILE, orders):
        return jsonify({"error": "Could not save order"}), 500

    whatsapp_payload = build_order_whatsapp_payload(order)
    return (
        jsonify(
            {
                "message": "Order submitted successfully",
                "order": order,
                "whatsappUrl": whatsapp_payload["webUrl"],
                "whatsappNumber": whatsapp_payload["number"],
                "whatsappText": whatsapp_payload["text"],
            }
        ),
        201,
    )


# ─── Admin Auth Routes ────────────────────────────────────────────────────────

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    payload = get_json_body()
    users = load_json(USERS_DATA_FILE, DEFAULT_USERS_DATA)

    input_username = str(payload.get("username", "")).strip()
    input_password = str(payload.get("password", ""))
    stored_username = str(users.get("username", ""))
    stored_password = str(users.get("password", ""))

    if input_username != stored_username or input_password != stored_password:
        return jsonify({"error": "Invalid username or password"}), 401

    response = make_response(jsonify({"message": "Login successful"}))
    is_production = os.environ.get("FLASK_ENV") == "production"
    response.set_cookie(
        COOKIE_NAME,
        stored_username,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="None" if is_production else "Lax",
        secure=is_production,
    )
    return response


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    response = make_response(jsonify({"message": "Logged out"}))
    response.delete_cookie(COOKIE_NAME, path="/")
    return response


@app.route("/api/admin/session", methods=["GET"])
def admin_session():
    username = get_authenticated_username()
    return jsonify({"authenticated": bool(username), "username": username})


# ─── Admin Data Routes ────────────────────────────────────────────────────────

@app.route("/api/admin/dashboard-data", methods=["GET"])
def admin_dashboard_data():
    _, error_response = require_auth()
    if error_response:
        return error_response

    data = load_site_data()
    data["enquiries"] = load_enquiries()
    data["orders"] = load_orders()
    return jsonify(data)


@app.route("/api/admin/enquiries", methods=["GET"])
def admin_enquiries():
    _, error_response = require_auth()
    if error_response:
        return error_response
    return jsonify({"enquiries": load_enquiries()})


@app.route("/api/admin/orders", methods=["GET"])
def admin_orders():
    _, error_response = require_auth()
    if error_response:
        return error_response
    return jsonify({"orders": load_orders()})


@app.route("/api/admin/enquiries/<enquiry_id>", methods=["DELETE"])
def delete_enquiry(enquiry_id):
    _, error_response = require_auth()
    if error_response:
        return error_response

    enquiries = load_enquiries()
    if not any(e.get("id") == enquiry_id for e in enquiries):
        return jsonify({"error": "Enquiry not found"}), 404

    enquiries = [e for e in enquiries if e.get("id") != enquiry_id]
    save_json(ENQUIRIES_DATA_FILE, enquiries)
    return jsonify({"message": "Enquiry removed", "enquiries": enquiries})


@app.route("/api/admin/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    _, error_response = require_auth()
    if error_response:
        return error_response

    orders = load_orders()
    if not any(o.get("id") == order_id for o in orders):
        return jsonify({"error": "Order not found"}), 404

    orders = [o for o in orders if o.get("id") != order_id]
    save_json(ORDERS_DATA_FILE, orders)
    return jsonify({"message": "Order removed", "orders": orders})


@app.route("/api/admin/business-info", methods=["PUT"])
def update_business_info():
    _, error_response = require_auth()
    if error_response:
        return error_response

    payload = get_json_body()
    required_fields = [
        "aboutText", "welcomeText", "phone", "whatsapp",
        "address", "email", "instagram", "facebook",
    ]
    cleaned = {}

    for field in required_fields:
        value = str(payload.get(field, "")).strip()
        if not value:
            return jsonify({"error": f"{field} is required"}), 400
        cleaned[field] = value

    data = load_site_data()
    data["business"] = cleaned
    save_json(SITE_DATA_FILE, data)
    return jsonify({"message": "Business information saved", "business": cleaned})


@app.route("/api/admin/service-descriptions", methods=["PUT"])
def update_service_descriptions():
    _, error_response = require_auth()
    if error_response:
        return error_response

    payload = get_json_body()
    required_fields = ["agriculture", "doors", "chogaths"]
    cleaned = {}

    for field in required_fields:
        value = str(payload.get(field, "")).strip()
        if not value:
            return jsonify({"error": f"{field} is required"}), 400
        cleaned[field] = value

    data = load_site_data()
    data["services"] = cleaned
    save_json(SITE_DATA_FILE, data)
    return jsonify({"message": "Service descriptions saved", "services": cleaned})


@app.route("/api/admin/photos/<category>", methods=["POST"])
def upload_photos(category):
    _, error_response = require_auth()
    if error_response:
        return error_response

    if category not in IMAGE_LIMITS:
        return jsonify({"error": "Invalid photo category"}), 400

    payload = get_json_body()
    files = payload.get("files", [])
    if not isinstance(files, list) or not files:
        return jsonify({"error": "No files provided"}), 400

    data = load_site_data()
    gallery = data["galleries"].get(category, [])

    if len(gallery) + len(files) > IMAGE_LIMITS[category]:
        return jsonify(
            {"error": f"{category} gallery allows maximum {IMAGE_LIMITS[category]} images"}
        ), 400

    new_entries = []
    for item in files:
        entry, error = persist_base64_file(item, category)
        if error:
            return jsonify({"error": error}), 400
        gallery.append(entry)
        new_entries.append(entry)

    data["galleries"][category] = gallery
    save_json(SITE_DATA_FILE, data)
    return jsonify({"message": "Images uploaded", "photos": gallery, "added": new_entries})


@app.route("/api/admin/photos/<category>/<photo_id>", methods=["DELETE"])
def delete_photo(category, photo_id):
    _, error_response = require_auth()
    if error_response:
        return error_response

    if category not in IMAGE_LIMITS:
        return jsonify({"error": "Invalid delete path"}), 400

    data = load_site_data()
    gallery = data["galleries"].get(category, [])
    target = next((p for p in gallery if p.get("id") == photo_id), None)
    if target is None:
        return jsonify({"error": "Photo not found"}), 404

    data["galleries"][category] = [p for p in gallery if p.get("id") != photo_id]
    save_json(SITE_DATA_FILE, data)

    # Remove the file from disk
    url_path = target.get("url", "").lstrip("/")
    file_path = ROOT_DIR / url_path
    if file_path.exists() and file_path.is_file():
        try:
            file_path.unlink()
        except OSError:
            pass

    return jsonify({"message": "Photo removed", "photos": data["galleries"][category]})


# ─── Uploads Serving ──────────────────────────────────────────────────────────

@app.route("/uploads/<path:filename>")
def uploaded_files(filename):
    return send_from_directory(UPLOADS_DIR, filename)


# ─── Entry Point ──────────────────────────────────────────────────────────────

ensure_project_files()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
