import sys
import datetime
import pytz
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


calendar_module_auth_credentials = None


def main():
    assistant = Jiro()
    # TODO: consider moving this to Jiro or the calendar module
    initialize_calendar_module()
    run_tests()

    # execution loop
    while(1):
        sys.stdout.write("> ")
        sys.stdout.flush()
        user_input: str = sys.stdin.readline()

        assistant.input_handler(user_input)


def initialize_calendar_module():
    global calendar_module_auth_credentials
    calendar_module_auth_credentials = authenticate_with_calendar_api()


class DayAnalytics:
    def __init__(self, total_committed_time=0):
        self.total_committed_time = total_committed_time

    def getCommittedHours(self):
        return self.total_committed_time / 3600.0


def run_calendar_cmdline():
    # TODO: do some date parsing
    target_start_date: datetime = None
    target_end_date: datetime = None

    # get start date
    sys.stdout.write("Enter start date: ")
    sys.stdout.flush()
    date_user_input: str = sys.stdin.readline().rstrip()

    if date_user_input == "today":
        target_start_date = datetime.datetime.today()
    else:
        try:
            target_start_date = datetime.datetime.strptime(date_user_input, "%Y-%m-%d")
        except:
            print("Unrecognized date... exiting")
            return

    # get end date
    sys.stdout.write("Enter end date (press 'Enter' for today): ")
    sys.stdout.flush()
    date_user_input: str = sys.stdin.readline().rstrip()

    if date_user_input == "" or date_user_input == "today":
        target_start_date = datetime.datetime.today()
    else:
        try:
            target_start_date = datetime.datetime.strptime(date_user_input, "%Y-%m-%d")
        except:
            print("Unrecognized date... exiting")
            return

    get_calendar_analytics(target_start_date, target_end_date)


def get_calendar_analytics(target_start_date: datetime, target_end_date: datetime = None):
    if target_end_date == None:
        target_end_date = target_start_date

    # filter for non-all day events
    events = filter(
        lambda event: 'dateTime' in event['start'],
        get_events(target_start_date, target_end_date, calendar_module_auth_credentials)
    )
    simplified_events = map(lambda event: event_transformer(event), events)

    day_analytics = DayAnalytics()

    if not simplified_events:
        print('No upcoming events found.')
    for event in simplified_events:
        event_length_seconds = (event['end'] - event['start']).seconds
        event_synopsis_string = f"{event['summary']}: {event_length_seconds / 3600.0}h"

        print(event_synopsis_string)
        day_analytics.total_committed_time += event_length_seconds

    print(f"Total committed hours: {day_analytics.getCommittedHours()}")


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


def get_events(
    target_date_start: datetime, 
    target_date_end: datetime,
    auth_credentials, 
    max_events: int = 100, 
):
    service = build('calendar', 'v3', credentials=auth_credentials)
    
    # If no end date supplied, default to the start date so we fetch the day 
    if target_date_end == None:
        target_date_end = target_date_start

    date_start = datetime.datetime(
        target_date_start.year, 
        target_date_start.month, 
        target_date_start.day, 
        hour=0, 
        minute=0, 
        second=0, 
        tzinfo=TIME_ZONE
    ).isoformat()
    date_end = datetime.datetime(
        target_date_end.year, 
        target_date_end.month, 
        target_date_end.day, 
        hour=23, 
        minute=59, 
        second=59, 
        tzinfo=TIME_ZONE
    ).isoformat()

    events_result = service.events().list(
        calendarId='primary', 
        timeMin=date_start, 
        timeMax=date_end, 
        maxResults=10, 
        singleEvents=True, 
        orderBy='startTime',
    ).execute()

    return events_result.get('items', [])


def event_transformer(event):
    return {
        'id': event['id'],
        'summary': event['summary'],

        # strip timezone off of the string and parse as datetime 
        'start': datetime.datetime.strptime(
            event['start']['dateTime'][:-6], 
            '%Y-%m-%dT%H:%M:%S'
        ),
        'end': datetime.datetime.strptime(
            event['end']['dateTime'][:-6], 
            '%Y-%m-%dT%H:%M:%S'
        ),
    }


def test_command_line_defaults() -> None:
    assistant = Jiro()
    assert assistant.get_intent("analyze week") == ANALYZE_WEEK_INTENT 
    assert assistant.get_intent("events") == EVENTS_INTENT 
    assert assistant.get_intent("quit") == QUIT_INTENT
    assert assistant.get_intent("exit") == QUIT_INTENT
    assert assistant.get_intent("test") == RUN_TEST


# TODO: make this test compatible with travis CI. For now just test locally
def local_test_get_events() -> None:
    auth_credentials = authenticate_with_calendar_api()
    test_day = datetime.datetime(year=2019, month=2, day=3)
    test_day_events = get_events(test_day, test_day, auth_credentials)

    assert len(test_day_events) == 2
    assert test_day_events[0]['summary'] == "Test event 1"
    assert test_day_events[1]['summary'] == "Test event 2"


def run_tests():
    print("\nRunning automated tests...")
    test_command_line_defaults()
    local_test_get_events()
    print("All tests passed!\n")


class Jiro:
    def __init__(self):
        return

    def input_handler(self, input_string: str) -> None:
        input_string: str = input_string.rstrip()

        intent: str = self.get_intent(input_string)

        if intent == QUIT_INTENT:
            quit(0)
        elif intent == UNKNOWN_INTENT:
            print("Unrecognized intent")
        elif intent == EVENTS_INTENT:
            run_calendar_cmdline()
        elif intent == ANALYZE_WEEK_INTENT:
            print("\nAnalyzing your week...\n")
            time_now = datetime.datetime.now()
            get_calendar_analytics(time_now, time_now + datetime.timedelta(days=7))
            print("\n")
        elif intent == RUN_TEST:
            print("running test")
        else:
            print("Invalid intent state")

        return None
    

    def get_intent(self, input_string: str) -> str:
        # TODO use NLP to get intent. For now just use string
        if input_string == "quit" or input_string == "exit":
            return QUIT_INTENT 
        elif input_string == "test":
            return RUN_TEST
        elif input_string == "events":
            return EVENTS_INTENT
        elif input_string == "analyze week":
            return ANALYZE_WEEK_INTENT
        else:
            return UNKNOWN_INTENT
    


RUN_TEST = "RunTest"
EVENTS_INTENT = "EventsToday"
ANALYZE_WEEK_INTENT = "AnalyzeWeek"
QUIT_INTENT = "Quit"
UNKNOWN_INTENT = "Unknown"
PACIFIC_TZ = "US/Pacific"
TIME_ZONE = pytz.timezone('US/Pacific')
# TIME_ZONE = None

if __name__ == "__main__":
    main()
