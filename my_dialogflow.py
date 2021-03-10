from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.exceptions import InvalidArgument
import os


def dialogflow_get():
    # dialogflow_project_id, dialogflow_language_code, session_id, key_json
    dialogflow_project_id = 'russianposttrackbot-yy9j'
    dialogflow_language_code = 'Ru-ru'
    session_id = 'current-user-id1'

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'D:\\Python\\RussianPostBot\\rp3.json'
    text_to_be_analyzed = "косяк"
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(dialogflow_project_id, session_id)
    text_input = dialogflow.types.TextInput({'text': text_to_be_analyzed, 'language_code': dialogflow_language_code})
    query_input = dialogflow.types.QueryInput({'text': text_input})
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)


def main():
    # text_messages('всё правильно')
    dialogflow_get()

if __name__ == '__main__':
    main()
