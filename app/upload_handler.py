from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
import platform
import ua_parser.user_agent_parser as ua_parser
from typing import Optional
import json
from datetime import datetime, timedelta
import os
import secrets
import hashlib
import re


router = APIRouter()

# Log file configuration
LOG_FILE = "student_access_log_G3.txt"
TOKEN_EXPIRY_MINUTES = 30  # Token valid for 30 minutes

def generate_device_fingerprint(request: Request) -> str:
    """Generate a persistent device fingerprint using multiple client characteristics"""
    # Get client headers and connection info
    client_port = str(request.client.port) if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    accept_language = request.headers.get("accept-language", "unknown")
    accept_encoding = request.headers.get("accept-encoding", "unknown")
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else str(request.client.host if request.client else "unknown")
    
    # Parse User-Agent for additional details
    ua_data = ua_parser.Parse(user_agent)
    browser_family = ua_data['user_agent']['family']  # e.g., "Chrome"
    os_family = ua_data['os']['family']  # e.g., "Windows"
    # Create a fingerprint hash from multiple components
    fingerprint_string = (
        f"{browser_family}:{os_family}:{client_port}:{client_ip}"
        f"{accept_language}:{accept_encoding}:"
        f"{x_forwarded_for.split(',')[0] if x_forwarded_for else ''}"
    )
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()

def generate_attendance_token(student_id: str) -> str:
    """Generate a unique, secure attendance token"""
    random_part = secrets.token_hex(16)
    timestamp = int(datetime.now().timestamp())
    return hashlib.sha256(f"{student_id}-{random_part}-{timestamp}".encode()).hexdigest()

def log_student_access(student_id: str, client_ip: str, user_agent: str, token: str, device_fingerprint: str):
    """Update existing log entry or create a new one if none exists"""
    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "student_id": student_id,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "token": token,
        "token_expiry": (datetime.now() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)).isoformat(),
        "device_fingerprint": device_fingerprint
    }

    entries = []

    # Load existing entries
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                content = f.read().strip()
                if content:
                    # Fix JSON format: strip trailing commas, wrap in []
                    content = re.sub(r",\s*}", "}", content)
                    content = re.sub(r",\s*]", "]", content)
                    if not content.startswith("["):
                        content = "[" + content + "]"
                    entries = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Failed to load existing log: {e}")

    # Update if student_id exists
    updated = False
    for entry in entries:
        if entry.get("student_id") == student_id:
            entry.update(new_entry)
            updated = True
            break

    if not updated:
        entries.append(new_entry)

    # Write updated log back to file
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)

    #print(f"{'Updated' if updated else 'Added'} student access log for ID {student_id}")


def get_logged_student_ids_from_file(log_file):
    student_ids = set()

    if not os.path.exists(log_file):
        print("Log file not found.")
        return student_ids

    with open(log_file, "r") as f:
        raw = f.read().strip()

    # Attempt to clean and format as valid JSON array
    if raw.startswith('{'):
        raw = "[" + raw + "]"
    elif raw.startswith('['):
        pass  # already an array
    else:
        print("Unrecognized JSON format.")
        return student_ids

    # Remove trailing commas before closing braces/brackets
    raw = re.sub(r",\s*}", "}", raw)
    raw = re.sub(r",\s*]", "]", raw)

    try:
        records = json.loads(raw)
        for record in records:
            student_id = record.get("student_id")
            if student_id:
                #print("Found student_id:", student_id)
                student_ids.add(student_id)
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON log file:", e)
        return student_ids

    #print("✅ Extracted student_ids:", student_ids)
    return student_ids

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    # File validation (unchanged)
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are allowed")

    contents = await file.read()
    text = contents.decode("utf-8").strip()

    if not text:
        raise HTTPException(status_code=400, detail="File is empty")

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    
    student_id = data.get("studentId")
    if not student_id:
        raise HTTPException(status_code=400, detail="Missing student ID")

    required_fields = {"studentId", "studentName", "subject"}
    if not required_fields.issubset(data):
        missing = required_fields - data.keys()
        raise HTTPException(status_code=400, detail=f"Missing fields: {', '.join(missing)}")
    
    
    valid_ids = get_logged_student_ids_from_file(LOG_FILE)
    #print(f"Checking student {student_id} against {len(valid_ids)} registered students")

    if str(student_id) not in valid_ids:
        # Add debug info to response
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"Student number {student_id} not found in my class",
                #"valid_ids": list(valid_ids),
                #"received_id": student_id
            }
        )

    # Get client info
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.client.host
    user_agent = request.headers.get("user-agent", "unknown")
    fingerprint = generate_device_fingerprint(request)
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error loading log file: {e}")
                entries = []
        fingerprints_used_by_others = []
        for record in entries:
            try:
                fingerprint_in_record = record.get("device_fingerprint")
                if fingerprint_in_record:
                    fingerprints_used_by_others.append(fingerprint_in_record)
                if str(record.get("student_id")) == str(student_id):
                    existing_fingerprint = record.get("device_fingerprint")
                    # print(student_id)
                    # print(fingerprint )
                    # print(existing_student_id)
                    # print(existing_fingerprint)
                    if fingerprint == existing_fingerprint and record.get("token")!="":
                        return JSONResponse(content={
        "attendance_token": record.get("token"),
        "message":"here is your token"
    })              
                    elif fingerprint in fingerprints_used_by_others:
                        return JSONResponse(content={
        "message":"this device has been used"
    })              
                    else:
                        # Generate attendance token
                        token = generate_attendance_token(data["studentId"])
                        
                        # Log the access with token
                        log_student_access(
                            student_id=data["studentId"],
                            client_ip=client_ip,
                            user_agent=user_agent,
                            token=token,
                            device_fingerprint=fingerprint
                        )

                        return JSONResponse(content={
                            "attendance_token": token,
                            "token_expiry_minutes": TOKEN_EXPIRY_MINUTES,
                        })
                        
            except (KeyError, ValueError) as e:
                print(f"Skipping malformed record: {e}")
                continue
    
    

@router.get("/mark-attendance/{student_id}/{token}")
async def mark_attendance(student_id: str, token: str):
    """Endpoint for students to mark attendance using their token"""

    if not os.path.exists(LOG_FILE):
        raise HTTPException(status_code=404, detail="No attendance records found")

    updated_lines = []
    attendance_marked = False

    try:
        with open(LOG_FILE, "r") as f:
            entries = json.load(f)  # Read the entire log file as a list of records

        for record in entries:
            if record.get("student_id") == student_id and record.get("token") == token:
                # Check token expiry
                expiry_time = datetime.fromisoformat(record["token_expiry"])
                if datetime.now() > expiry_time:
                    raise HTTPException(status_code=410, detail="Token has expired")

                # Mark attendance by updating the record
                record["attendance_marked"] = True
                record["marked_at"] = datetime.now().isoformat()
                attendance_marked = True

            updated_lines.append(record)

        if not attendance_marked:
            raise HTTPException(status_code=403, detail="No token or student ID Found")

        # Rewrite the file with updated records
        with open(LOG_FILE, "w") as f:
            json.dump(updated_lines, f, indent=4)  # Write the updated records as JSON

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

    return {
        "status": "attendance_marked I will see you next class",
        "student_id": student_id,
        "timestamp": datetime.now().isoformat()
    }