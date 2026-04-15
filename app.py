import base64
import hashlib
import hmac
import json
import mimetypes
import os
import posixpath
import secrets
import smtplib
import time
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from email.message import EmailMessage
from urllib.parse import quote, unquote, urlparse


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
UPLOADS_DIR = ROOT_DIR / "uploads"
JS_DIR = ROOT_DIR / "js"

SITE_DATA_FILE = DATA_DIR / "site-data.json"
ADMIN_DATA_FILE = DATA_DIR / "admin.json"
ENQUIRIES_DATA_FILE = DATA_DIR / "enquiries.json"
ORDERS_DATA_FILE = DATA_DIR / "orders.json"

DEFAULT_SITE_DATA = {
    "business": {
        "aboutText": (
            "Momi Repairing Works offers dependable repairing and fabrication work "
            "for agriculture machines, main doors and chogaths."
        ),
        "welcomeText": (
            "We provide high quality repairing and manufacturing services for "
            "agriculture machines, main doors and chogaths. Our goal is to deliver "
            "strong, durable and reliable work with customer satisfaction."
        ),
        "phone": "+91 98765 43210",
        "whatsapp": "+91 98765 43210",
        "address": "Your workshop address, city, state",
        "email": "momiworks@example.com",
        "instagram": "https://www.instagram.com/",
        "facebook": "https://www.facebook.com/",
        "address" : "https://www.google.co.in/maps"
    },
    "services": {
        "agriculture": {
            "description": (
                "Repairing, welding and maintenance support for agriculture machines "
                "that need strong and long-lasting performance."
            ),
            "enabled": True,
        },
        "doors": {
            "description": (
                "Custom-built and repaired main doors made with durable materials, "
                "solid fitting and a neat finish."
            ),
            "enabled": True,
        },
        "chogaths": {
            "description": (
                "Strong, custom-sized chogaths created for long life, reliable support "
                "and clean installation."
            ),
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

DEFAULT_ADMIN_DATA = {
    "username": "admin",
    "passwordHash": "16be0250220758ca16ac5b204d3db262363bb86c50cd7b07d8b3a03895480a86",
}

DEFAULT_ENQUIRIES = []
DEFAULT_ORDERS = []

IMAGE_LIMITS = {
    "admin": 8,
    "agriculture": 6,
    "doors": 6,
    "chogaths": 4,
}

COOKIE_NAME = "adminAuth"
SESSION_MAX_AGE = 12 * 60 * 60
SECRET_KEY = os.environ.get("MRW_SECRET_KEY", "change-this-secret-for-production")


def ensure_project_files():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOADS_DIR.mkdir(exist_ok=True)
    JS_DIR.mkdir(exist_ok=True)

    if not SITE_DATA_FILE.exists():
        SITE_DATA_FILE.write_text(json.dumps(DEFAULT_SITE_DATA, indent=2), encoding="utf-8")

    if not ADMIN_DATA_FILE.exists():
        ADMIN_DATA_FILE.write_text(json.dumps(DEFAULT_ADMIN_DATA, indent=2), encoding="utf-8")

    if not ENQUIRIES_DATA_FILE.exists():
        ENQUIRIES_DATA_FILE.write_text(json.dumps(DEFAULT_ENQUIRIES, indent=2), encoding="utf-8")

    if not ORDERS_DATA_FILE.exists():
        ORDERS_DATA_FILE.write_text(json.dumps(DEFAULT_ORDERS, indent=2), encoding="utf-8")

    for category in IMAGE_LIMITS:
        (UPLOADS_DIR / category).mkdir(exist_ok=True)


def load_json(path, fallback):
    if not path.exists():
        return json.loads(json.dumps(fallback))
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def sign_value(value):
    return hmac.new(SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def build_session_token(username):
    issued_at = str(int(time.time()))
    nonce = secrets.token_hex(8)
    payload = f"{username}.{issued_at}.{nonce}"
    signature = sign_value(payload)
    return f"{payload}.{signature}"


def verify_session_token(token):
    parts = token.split(".")
    if len(parts) != 4:
        return None

    username, issued_at, nonce, signature = parts
    payload = f"{username}.{issued_at}.{nonce}"
    expected_signature = sign_value(payload)

    if not hmac.compare_digest(signature, expected_signature):
        return None

    try:
        issued_at_int = int(issued_at)
    except ValueError:
        return None

    if time.time() - issued_at_int > SESSION_MAX_AGE:
        return None

    return username


class AppHandler(BaseHTTPRequestHandler):
    server_version = "MRWBackend/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Public data (no auth required)
        if path == "/api/public/site-data":
            self.handle_public_site_data()
            return

        # Admin API should be authenticated
        if path == "/api/admin/session":
            self.handle_admin_session()
            return

        if path == "/api/admin/dashboard-data":
            self.require_auth(self.handle_admin_dashboard_data)
            return

        if path == "/api/admin/enquiries":
            self.require_auth(self.handle_admin_enquiries)
            return

        if path == "/api/admin/orders":
            self.require_auth(self.handle_admin_orders)
            return

        if path == "/login":
            self.serve_admin_login()
            return

        if path == "/admin":
            username = self.get_authenticated_username()
            if not username:
                self.send_response(HTTPStatus.FOUND)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            self.serve_admin_dashboard()
            return

        if path in ["/admin-dashboard", "/admin-dashboard.html"]:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/admin")
            self.end_headers()
            return

        # Block direct file access to admin pages so only clean routes work
        if path in ["/admin-login.html", "/admin.html", "/dashboard.html"]:
            self.send_error(HTTPStatus.NOT_FOUND, "Unauthorized access")
            return

        if path.startswith("/admin/"):
            self.send_error(HTTPStatus.FORBIDDEN, "Unauthorized access")
            return

        # Fallback static assets/page
        self.serve_static(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/admin/login":
            self.handle_admin_login()
            return

        # Protect dashboard modifications via auth
        if path == "/api/admin/logout":
            self.handle_admin_logout()
            return

        if path == "/api/admin/logout":
            self.handle_admin_logout()
            return

        if path == "/api/public/enquiries":
            self.handle_public_enquiry_submit()
            return

        if path == "/api/public/orders":
            self.handle_public_order_submit()
            return

        if path.startswith("/api/admin/photos/"):
            self.require_auth(lambda: self.handle_photo_upload(path))
            return

        self.send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/admin/business-info":
            self.require_auth(self.handle_business_update)
            return

        if path == "/api/admin/service-descriptions":
            self.require_auth(self.handle_service_update)
            return

        self.send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/admin/enquiries/"):
            self.require_auth(lambda: self.handle_enquiry_delete(path))
            return

        if path.startswith("/api/admin/orders/"):
            self.require_auth(lambda: self.handle_order_delete(path))
            return

        if path.startswith("/api/admin/photos/"):
            self.require_auth(lambda: self.handle_photo_delete(path))
            return

        self.send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)

    def log_message(self, format, *args):
        return

    def require_auth(self, callback):
        username = self.get_authenticated_username()
        if not username:
            self.send_json({"error": "Unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
            return
        callback()

    def get_authenticated_username(self):
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None

        cookie = SimpleCookie()
        cookie.load(cookie_header)
        morsel = cookie.get(COOKIE_NAME)
        if morsel is None:
            return None

        return verify_session_token(morsel.value)

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length == 0:
            return {}

        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON payload")

    def send_json(self, payload, status=HTTPStatus.OK, headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def serve_static(self, path):
        relative_path = path or "/"
        if relative_path == "/":
            relative_path = "/index.html"

        safe_path = posixpath.normpath(unquote(relative_path)).lstrip("/")
        file_path = (ROOT_DIR / safe_path).resolve()

        if not str(file_path).startswith(str(ROOT_DIR.resolve())):
            self.send_error(HTTPStatus.FORBIDDEN)
            return

        if file_path.is_dir():
            file_path = file_path / "index.html"

        if not file_path.exists() or not file_path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def load_site_data(self):
        data = load_json(SITE_DATA_FILE, DEFAULT_SITE_DATA)
        data.setdefault("business", {})
        data.setdefault("services", {})
        data.setdefault("galleries", {})
        for category in IMAGE_LIMITS:
            data["galleries"].setdefault(category, [])
        return data

    def handle_public_site_data(self):
        data = self.load_site_data()
        self.send_json(data)

    def handle_admin_session(self):
        username = self.get_authenticated_username()
        self.send_json({"authenticated": bool(username), "username": username})

    def serve_admin_login(self):
        file_path = ROOT_DIR / "admin-login.html"
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_admin_dashboard(self):
        file_path = ROOT_DIR / "admin.html"
        if not file_path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(str(file_path))
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def serve_forbidden(self):
        self.send_error(HTTPStatus.FORBIDDEN, "Unauthorized access")

    def handle_admin_dashboard_data(self):
        data = self.load_site_data()
        data["enquiries"] = self.load_enquiries()
        data["orders"] = self.load_orders()
        self.send_json(data)

    def handle_admin_enquiries(self):
        self.send_json({"enquiries": self.load_enquiries()})

    def handle_admin_orders(self):
        self.send_json({"orders": self.load_orders()})

    def handle_enquiry_delete(self, path):
        enquiry_id = path.removeprefix("/api/admin/enquiries/").strip("/")
        if not enquiry_id:
            self.send_json({"error": "Invalid enquiry id"}, status=HTTPStatus.BAD_REQUEST)
            return

        enquiries = self.load_enquiries()
        target = next((enquiry for enquiry in enquiries if enquiry.get("id") == enquiry_id), None)
        if target is None:
            self.send_json({"error": "Enquiry not found"}, status=HTTPStatus.NOT_FOUND)
            return

        enquiries = [enquiry for enquiry in enquiries if enquiry.get("id") != enquiry_id]
        save_json(ENQUIRIES_DATA_FILE, enquiries)
        self.send_json({"message": "Enquiry removed", "enquiries": enquiries})

    def handle_admin_login(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        admin = load_json(ADMIN_DATA_FILE, DEFAULT_ADMIN_DATA)
        username = str(payload.get("username", "")).strip()
        password = str(payload.get("password", ""))

        if username != admin["username"] or hash_password(password) != admin["passwordHash"]:
            self.send_json({"error": "Invalid username or password"}, status=HTTPStatus.UNAUTHORIZED)
            return

        token = build_session_token(username)
        headers = {
            "Set-Cookie": (
                f"{COOKIE_NAME}={token}; HttpOnly; Path=/; Max-Age={SESSION_MAX_AGE}; SameSite=Lax"
            )
        }
        self.send_json({"message": "Login successful"}, headers=headers)

    def handle_admin_logout(self):
        headers = {
            "Set-Cookie": f"{COOKIE_NAME}=deleted; HttpOnly; Path=/; Max-Age=0; SameSite=Lax"
        }
        self.send_json({"message": "Logged out"}, headers=headers)

    def handle_public_enquiry_submit(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        required_fields = ["name", "phone", "service", "message"]
        enquiry = {}
        for field in required_fields:
            value = str(payload.get(field, "")).strip()
            if not value:
                self.send_json({"error": f"{field} is required"}, status=HTTPStatus.BAD_REQUEST)
                return
            enquiry[field] = value

        enquiry["email"] = str(payload.get("email", "")).strip()
        enquiry["id"] = uuid.uuid4().hex
        enquiry["createdAt"] = now_iso()

        enquiries = self.load_enquiries()
        enquiries.insert(0, enquiry)
        save_json(ENQUIRIES_DATA_FILE, enquiries)
        self.send_enquiry_email(enquiry)
        self.send_json({"message": "Enquiry submitted successfully", "enquiry": enquiry}, status=HTTPStatus.CREATED)

    def handle_public_order_submit(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        service = str(payload.get("service", "")).strip()
        fields = payload.get("fields", {})
        if service not in {"agriculture", "doors", "chogaths"}:
            self.send_json({"error": "Invalid service selected"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(fields, dict):
            self.send_json({"error": "Invalid order fields"}, status=HTTPStatus.BAD_REQUEST)
            return

        validator = getattr(self, f"validate_{service}_order")
        normalized, error = validator(fields)
        if error:
            self.send_json({"error": error}, status=HTTPStatus.BAD_REQUEST)
            return

        order = {
            "id": uuid.uuid4().hex,
            "service": service,
            "label": self.get_service_label(service),
            "fields": normalized,
            "createdAt": now_iso(),
        }
        orders = self.load_orders()
        orders.insert(0, order)
        save_json(ORDERS_DATA_FILE, orders)

        whatsapp_payload = self.build_order_whatsapp_payload(order)
        self.send_json(
            {
                "message": "Order submitted successfully",
                "order": order,
                "whatsappUrl": whatsapp_payload["webUrl"],
                "whatsappNumber": whatsapp_payload["number"],
                "whatsappText": whatsapp_payload["text"],
            },
            status=HTTPStatus.CREATED,
        )

    def handle_business_update(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        required_fields = [
            "aboutText",
            "welcomeText",
            "phone",
            "whatsapp",
            "address",
            "email",
            "instagram",
            "facebook",
        ]

        cleaned = {}
        for field in required_fields:
            value = str(payload.get(field, "")).strip()
            if not value:
                self.send_json({"error": f"{field} is required"}, status=HTTPStatus.BAD_REQUEST)
                return
            cleaned[field] = value

        data = self.load_site_data()
        data["business"] = cleaned
        save_json(SITE_DATA_FILE, data)
        self.send_json({"message": "Business information saved", "business": cleaned})

    def handle_service_update(self):
        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        required_fields = ["agriculture", "doors", "chogaths"]
        cleaned = {}
        for field in required_fields:
            value = str(payload.get(field, "")).strip()
            if not value:
                self.send_json({"error": f"{field} is required"}, status=HTTPStatus.BAD_REQUEST)
                return
            cleaned[field] = value

        data = self.load_site_data()
        data["services"] = cleaned
        save_json(SITE_DATA_FILE, data)
        self.send_json({"message": "Service descriptions saved", "services": cleaned})

    def handle_photo_upload(self, path):
        category = path.removeprefix("/api/admin/photos/").strip("/")
        if category not in IMAGE_LIMITS:
            self.send_json({"error": "Invalid photo category"}, status=HTTPStatus.BAD_REQUEST)
            return

        try:
            payload = self.read_json_body()
        except ValueError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        files = payload.get("files", [])
        if not isinstance(files, list) or not files:
            self.send_json({"error": "No files provided"}, status=HTTPStatus.BAD_REQUEST)
            return

        data = self.load_site_data()
        gallery = data["galleries"].get(category, [])

        if len(gallery) + len(files) > IMAGE_LIMITS[category]:
            self.send_json(
                {"error": f"{category} gallery allows maximum {IMAGE_LIMITS[category]} images"},
                status=HTTPStatus.BAD_REQUEST,
            )
            return

        new_entries = []
        for item in files:
            entry, error = self.persist_base64_file(item, category)
            if error:
                self.send_json({"error": error}, status=HTTPStatus.BAD_REQUEST)
                return
            gallery.append(entry)
            new_entries.append(entry)

        data["galleries"][category] = gallery
        save_json(SITE_DATA_FILE, data)
        self.send_json({"message": "Images uploaded", "photos": gallery, "added": new_entries})

    def handle_photo_delete(self, path):
        parts = path.split("/")
        if len(parts) != 6:
            self.send_json({"error": "Invalid delete path"}, status=HTTPStatus.BAD_REQUEST)
            return

        _, api, admin, photos, category, photo_id = parts
        if api != "api" or admin != "admin" or photos != "photos" or category not in IMAGE_LIMITS:
            self.send_json({"error": "Invalid delete path"}, status=HTTPStatus.BAD_REQUEST)
            return

        data = self.load_site_data()
        gallery = data["galleries"].get(category, [])
        target = next((photo for photo in gallery if photo.get("id") == photo_id), None)

        if target is None:
            self.send_json({"error": "Photo not found"}, status=HTTPStatus.NOT_FOUND)
            return

        gallery = [photo for photo in gallery if photo.get("id") != photo_id]
        data["galleries"][category] = gallery
        save_json(SITE_DATA_FILE, data)

        file_path = ROOT_DIR / target["url"].lstrip("/")
        if file_path.exists():
            file_path.unlink()

        self.send_json({"message": "Photo removed", "photos": gallery})

    def load_enquiries(self):
        enquiries = load_json(ENQUIRIES_DATA_FILE, DEFAULT_ENQUIRIES)
        if isinstance(enquiries, list):
            return enquiries
        return []

    def load_orders(self):
        orders = load_json(ORDERS_DATA_FILE, DEFAULT_ORDERS)
        if isinstance(orders, list):
            return orders
        return []

    def handle_order_delete(self, path):
        order_id = path.removeprefix("/api/admin/orders/").strip("/")
        if not order_id:
            self.send_json({"error": "Invalid order id"}, status=HTTPStatus.BAD_REQUEST)
            return

        orders = self.load_orders()
        target = next((order for order in orders if order.get("id") == order_id), None)
        if target is None:
            self.send_json({"error": "Order not found"}, status=HTTPStatus.NOT_FOUND)
            return

        orders = [order for order in orders if order.get("id") != order_id]
        save_json(ORDERS_DATA_FILE, orders)
        self.send_json({"message": "Order removed", "orders": orders})

    def validate_agriculture_order(self, fields):
        required = [
            "machineName",
            "weight",
            "color",
            "comment",
            "customerName",
            "phone",
        ]
        return self.validate_required_fields(fields, required)

    def validate_doors_order(self, fields):
        required = [
            "doorType",
            "size",
            "weight",
            "color",
            "customerName",
            "phone",
        ]
        cleaned, error = self.validate_required_fields(fields, required)
        if error:
            return None, error
        if cleaned["doorType"] not in {"Main", "Normal"}:
            return None, "Door type must be Main or Normal"
        return cleaned, None

    def validate_chogaths_order(self, fields):
        required = [
            "sizeOption",
            "weight",
            "customerName",
            "phone",
        ]
        cleaned, error = self.validate_required_fields(fields, required)
        if error:
            return None, error
        cleaned["customSize"] = str(fields.get("customSize", "")).strip()
        cleaned["companyName"] = str(fields.get("companyName", "")).strip()
        return cleaned, None

    def validate_required_fields(self, fields, required):
        cleaned = {}
        for field in required:
            value = str(fields.get(field, "")).strip()
            if not value:
                return None, f"{field} is required"
            cleaned[field] = value
        return cleaned, None

    def get_service_label(self, service):
        labels = {
            "agriculture": "Agricultural Machine",
            "doors": "Main Door",
            "chogaths": "Chogath",
        }
        return labels.get(service, service)

    def build_order_whatsapp_payload(self, order):
        business = self.load_site_data().get("business", {})
        whatsapp_number = self.normalize_phone_number(business.get("whatsapp") or business.get("phone") or "")
        if not whatsapp_number:
            return {"number": "", "text": "", "webUrl": ""}

        lines = [f"New Order: {order['label']}"]
        for key, value in order["fields"].items():
            if value:
                lines.append(f"{self.pretty_label(key)}: {value}")
        lines.append(f"Submitted At: {order['createdAt']}")
        raw_text = "\n".join(lines)
        message = quote(raw_text)
        return {
            "number": whatsapp_number,
            "text": raw_text,
            "webUrl": f"https://wa.me/{whatsapp_number}?text={message}",
        }

    def normalize_phone_number(self, value):
        return "".join(char for char in str(value) if char.isdigit())

    def pretty_label(self, value):
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

    def persist_base64_file(self, item, category):
        if not isinstance(item, dict):
            return None, "Invalid file payload"

        original_name = str(item.get("name", "image")).strip() or "image"
        data_url = str(item.get("dataUrl", "")).strip()
        if not data_url.startswith("data:image/") or ";base64," not in data_url:
            return None, "Only image data URLs are supported"

        header, encoded = data_url.split(";base64,", 1)
        mime_type = header.removeprefix("data:")
        extension = mimetypes.guess_extension(mime_type) or ".png"
        filename = f"{uuid.uuid4().hex}{extension}"
        output_path = UPLOADS_DIR / category / filename

        try:
            file_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error):
            return None, "Invalid base64 image data"

        output_path.write_bytes(file_bytes)
        return {
            "id": uuid.uuid4().hex,
            "filename": original_name,
            "url": f"/uploads/{category}/{filename}",
            "uploadedAt": now_iso(),
        }, None

    def send_enquiry_email(self, enquiry):
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


def create_server(host="127.0.0.1", port=8000):
    ensure_project_files()
    return ThreadingHTTPServer((host, port), AppHandler)


def main():
    host = os.environ.get("MRW_HOST", "127.0.0.1")
    port = int(os.environ.get("MRW_PORT", "8000"))
    server = create_server(host=host, port=port)
    print(f"Momi Repairing Works backend running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
