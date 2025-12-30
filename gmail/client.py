def get_gmail_service():
    creds = authenticate_gmail(SCOPES)
    return build("gmail", "v1", credentials=creds)
