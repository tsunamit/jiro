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


def get_day_analytics():
    auth_credentials = authenticate_with_calendar_api()
    events = get_events_on_day(auth_credentials)
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

def get_events_on_day(auth_credentials):
    service = build('calendar', 'v3', credentials=auth_credentials)

    # get todays date
    today = datetime.datetime.today()
    today_start = datetime.datetime(
        today.year, today.month, today.day, 
        0, 0, 0, 0, None).isoformat() + 'Z'
    today_end = datetime.datetime(
        today.year, today.month, today.day, 
        23, 59, 59, 59, None).isoformat() + 'Z'

    events_result = service.events().list(calendarId='primary', timeMin=today_start,
                                        timeMax=today_end, maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()

    return events_result.get('items', [])

def event_transformer(event):
    return {
        'id': event['id'],
        'summary': event['summary'],
    }

def test_command_line_defaults() -> None:
    assistant = Jiro()
    assert assistant.get_intent("events today") == EVENTS_TODAY 
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
            get_day_analytics()
        elif intent == EVENTS_TODAY:
            get_day_analytics()
        else:
            print("Invalid intent state")

        return None
    

    def get_intent(self, input_string: str) -> str:
        # TODO use NLP to get intent. For now just use string
        if input_string == "quit" or input_string == "exit":
            return QUIT_INTENT 
        elif input_string == "test":
            return RUN_TEST
        elif input_string == "events today":
            return EVENTS_TODAY
        else:
            return UNKNOWN_INTENT
    


RUN_TEST = "RunTest"
EVENTS_TODAY = "EventsToday"
QUIT_INTENT = "Quit"
UNKNOWN_INTENT = "Unknown"

if __name__ == "__main__":
    main()
