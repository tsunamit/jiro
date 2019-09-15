import sys


def main():
    assistant = Jiro()

    # Execution loop
    while(1):
        sys.stdout.write("> ")
        sys.stdout.flush()

        user_input: str = sys.stdin.readline()

        assistant.input_handler(user_input)


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
