def parse_message(service, user_id, message_id):
    msg = service.users().messages().get(
        userId=user_id,
        id=message_id,
        format="full"
    ).execute()

    parsed = ParsedEmail()
    walk_parts(service, user_id, message_id, msg["payload"], parsed)
    return parsed


def walk_parts(service, user_id, msg_id, part, parsed: ParsedEmail):
    mime_type = part.get("mimeType")
    body = part.get("body", {})
    filename = part.get("filename")

    # TEXT
    if mime_type == "text/plain" and "data" in body:
        parsed.text += decode_base64(body["data"]) + "\n"

    elif mime_type == "text/html" and "data" in body:
        parsed.html += decode_base64(body["data"]) + "\n"

    # IMAGE
    elif mime_type.startswith("image/") and body.get("attachmentId"):
        att = service.users().messages().attachments().get(
            userId=user_id,
            messageId=msg_id,
            id=body["attachmentId"]
        ).execute()

        image = {
            "mimeType": mime_type,
            "data": base64.urlsafe_b64decode(att["data"]),
            "filename": filename
        }

        if filename:
            parsed.attachments.append(image)
        else:
            parsed.inline_images.append(image)

    # OTHER ATTACHMENTS
    elif filename and body.get("attachmentId"):
        att = service.users().messages().attachments().get(
            userId=user_id,
            messageId=msg_id,
            id=body["attachmentId"]
        ).execute()

        parsed.attachments.append({
            "filename": filename,
            "mimeType": mime_type,
            "data": base64.urlsafe_b64decode(att["data"])
        })

    # RECURSE
    for subpart in part.get("parts", []):
        walk_parts(service, user_id, msg_id, subpart, parsed)
