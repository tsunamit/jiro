import sys
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


def main():
    assistant = Jiro()

    # Execution loop
    while(1):
        sys.stdout.write("> ")
        sys.stdout.flush()

        user_input: str = sys.stdin.readline()

        assistant.input_handler(user_input)


def get_day_analytics(target_date):
    auth_credentials = authenticate_with_calendar_api()
    query_date = date_to_date_query_transformer(target_date)
    events = get_events_on_day(query_date, auth_credentials)
    simplified_events = map(lambda event: event_transformer(event), events)

    if not simplified_events:
        print('No upcoming events found.')
    for event in simplified_events:
        print(event)

def authenticate_with_calendar_api():
    creds = None
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',
                scopes
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def date_to_date_query_transformer(target_date):
    return target_date

def get_events_on_day(query_date, auth_credentials):
    service = build('calendar', 'v3', credentials=auth_credentials)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time

    events_result = service.events().list(calendarId='primary', timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()

    return events_result.get('items', [])

def event_transformer(event):
    return {
        'id': event['id'],
        'summary': event['summary'],
    }

def test_command_line_defaults() -> None:
    assistant = Jiro()
    assert assistant.get_intent("quit") == QUIT_INTENT
    assert assistant.get_intent("exit") == QUIT_INTENT
    assert assistant.get_intent("test") == RUN_TEST


class Jiro:
    def __init__(self):
        print("Jiro Online")
    

    def input_handler(self, input_string: str) -> None:
        input_string: str = input_string.rstrip()

        intent: str = self.get_intent(input_string)

        if intent == QUIT_INTENT:
            quit(0)
        elif intent == UNKNOWN_INTENT:
            print("Unrecognized intent")
        elif intent == RUN_TEST:
            print("running test")
            get_day_analytics(None)
        else:
            print("Invalid intent state")

        return None
    

    def get_intent(self, input_string: str) -> str:
        # TODO use NLP to get intent. For now just use string
        if input_string == "quit" or input_string == "exit":
            return QUIT_INTENT 
        elif input_string == "test":
            return RUN_TEST
        else:
            return UNKNOWN_INTENT
    


RUN_TEST = "RunTest"
PROCESS_IMAGE_INTENT = "ProcessImage"
QUIT_INTENT = "Quit"
UNKNOWN_INTENT = "Unknown"

if __name__ == "__main__":
    main()
