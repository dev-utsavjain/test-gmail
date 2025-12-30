# import os.path
# import base64
# from email.utils import parsedate_to_datetime

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

# # Read-only Gmail access (safe for PoC)
# SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# def authenticate_gmail():
#     creds = None

#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)

#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)

#         with open("token.json", "w") as token:
#             token.write(creds.to_json())

#     return creds


# def get_header(headers, name):
#     for h in headers:
#         if h["name"].lower() == name.lower():
#             return h["value"]
#     return None


# def fetch_latest_emails(max_results):
#     creds = authenticate_gmail()
#     service = build("gmail", "v1", credentials=creds)

#     results = service.users().messages().list(
#         userId="me",
#         maxResults=max_results
#     ).execute()

#     messages = results.get("messages", [])

#     for msg in messages:
#         msg_data = service.users().messages().get(
#             userId="me",
#             id=msg["id"],
#             format="full"
#         ).execute()

#         payload = msg_data["payload"]

#         parsed = {
#             "text": "",
#             "html": "",
#             "inline_images": [],
#             "attachments": []
#         }

#         walk_parts(service, "me", msg["id"], payload, parsed)

#         print("—" * 50)
#         print("TEXT:")
#         print(parsed["text"][:5000] if parsed["text"] else "[none]")

#         print(f"\nInline images: {len(parsed['inline_images'])}")
#         print(f"Attachments: {len(parsed['attachments'])}")

        

# def decode_base64(data):
#     return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")


# def walk_parts(service, user_id, msg_id, part, result):
#     mime_type = part.get("mimeType")
#     body = part.get("body", {})
#     filename = part.get("filename")

#     # TEXT
#     if mime_type == "text/plain" and "data" in body:
#         result["text"] += decode_base64(body["data"]) + "\n"

#     elif mime_type == "text/html" and "data" in body:
#         result["html"] += decode_base64(body["data"]) + "\n"

#     # IMAGE
#     elif mime_type.startswith("image/") and body.get("attachmentId"):
#         att = service.users().messages().attachments().get(
#             userId=user_id,
#             messageId=msg_id,
#             id=body["attachmentId"]
#         ).execute()

#         image = {
#             "mimeType": mime_type,
#             "data": base64.urlsafe_b64decode(att["data"]),
#             "filename": filename
#         }

#         if filename:
#             result["attachments"].append(image)
#         else:
#             result["inline_images"].append(image)

#     # OTHER ATTACHMENTS
#     elif filename and body.get("attachmentId"):
#         att = service.users().messages().attachments().get(
#             userId=user_id,
#             messageId=msg_id,
#             id=body["attachmentId"]
#         ).execute()

#         result["attachments"].append({
#             "filename": filename,
#             "mimeType": mime_type,
#             "data": base64.urlsafe_b64decode(att["data"])
#         })

#     # RECURSE
#     for subpart in part.get("parts", []):
#         walk_parts(service, user_id, msg_id, subpart, result)


# if __name__ == "__main__":
#     fetch_latest_emails(10)

def fetch_latest_emails(max_results=10):
    service = get_gmail_service()

    results = service.users().messages().list(
        userId="me",
        maxResults=max_results
    ).execute()

    for msg in results.get("messages", []):
        parsed = parse_message(service, "me", msg["id"])

        print("—" * 50)
        print("TEXT:")
        print(parsed.text[:5000] if parsed.text else "[none]")
        print(f"Inline images: {len(parsed.inline_images)}")
        print(f"Attachments: {len(parsed.attachments)}")
        
def decode_base64(data):
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

if __name__ == "__main__":
    fetch_latest_emails(10)