import os.path
import base64
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Read-only Gmail access (safe for PoC)
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate_gmail():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def get_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return None


def fetch_latest_emails(max_results=5):
    creds = authenticate_gmail()
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    messages = results.get("messages", [])

    for msg in messages:
        msg_data = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()

    #     headers = msg_data["payload"]["headers"]

    #     sender = get_header(headers, "From")
    #     subject = get_header(headers, "Subject")
    #     date_raw = get_header(headers, "Date")

    #     date = parsedate_to_datetime(date_raw) if date_raw else None

    #     print("—" * 50)
    #     print(f"From   : {sender}")
    #     print(f"Subject: {subject}")
    #     print(f"Date   : {date}")
    
    msg_data = service.users().messages().get(
        userId="me",
        id=msg["id"],
        format="full"
    ).execute()

    payload = msg_data["payload"]

    parsed = {  
            "text": None,
            #"html": None,
            "inline_images": [],
            "attachments": []
            }

    walk_parts(service, "me", msg["id"], payload, parsed)

    print("—" * 50)
    print("TEXT:")
    print(parsed["text"][:5000] if parsed["text"] else "[none]")

    # print("\nHTML:")
    # print(parsed["html"][:500] if parsed["html"] else "[none]")

    print(f"\nInline images: {len(parsed['inline_images'])}")
    print(f"Attachments: {len(parsed['attachments'])}")

        

def decode_base64(data):
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


def walk_parts(service, user_id, msg_id, part, result):
    mime_type = part.get("mimeType")
    body = part.get("body", {})
    filename = part.get("filename")

    # TEXT
    if mime_type == "text/plain" and "data" in body:
        result["text"] = decode_base64(body["data"])

    elif mime_type == "text/html" and "data" in body:
        result["html"] = decode_base64(body["data"])

    # INLINE IMAGE
    elif mime_type.startswith("image/"):
        attachment_id = body.get("attachmentId")
        if attachment_id:
            att = service.users().messages().attachments().get(
                userId=user_id,
                messageId=msg_id,
                id=attachment_id
            ).execute()

            result["inline_images"].append({
                "mimeType": mime_type,
                "data": base64.urlsafe_b64decode(att["data"]),
                "filename": filename
            })

    # ATTACHMENT (non-inline)
    elif filename and body.get("attachmentId"):
        att = service.users().messages().attachments().get(
            userId=user_id,
            messageId=msg_id,
            id=body["attachmentId"]
        ).execute()

        result["attachments"].append({
            "filename": filename,
            "mimeType": mime_type,
            "data": base64.urlsafe_b64decode(att["data"])
        })

    # RECURSE
    for subpart in part.get("parts", []):
        walk_parts(service, user_id, msg_id, subpart, result)



if __name__ == "__main__":
    fetch_latest_emails(1)
