from google.cloud import dialogflow_v2 as dialogflow
from google.api_core.exceptions import InvalidArgument
import os


'''
# Может быть когда-то пригодится, но надо разбираться, пока это не работает
def dialogfollow_auth_get():
    google.oauth2.
    credentials = google.oauth2.service_account.from_service_account_file(
        './Peepl-cb1dac99bdc0.json',
        scopes=['https://www.googleapis.com/auth/cloud-platform'])
'''


def dialogflow_init(key_json):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(key_json)


def dialogflow_get(dialogflow_settings, session_id, message_text):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(dialogflow_settings['dialogflow_project_id'], session_id)
    text_input = dialogflow.types.TextInput({'text': message_text,
                                             'language_code': dialogflow_settings['dialogflow_language_code']})
    query_input = dialogflow.types.QueryInput({'text': text_input})
    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)

    return response.query_result.fulfillment_text


def dialogflow_send_event(dialogflow_settings, session_id, event_name):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(dialogflow_settings['dialogflow_project_id'], session_id)
    event_input = dialogflow.types.EventInput({'name': event_name,
                                               'language_code': dialogflow_settings['dialogflow_language_code']})

    query_input = dialogflow.types.QueryInput({'event': event_input})

    try:
        response = session_client.detect_intent(session=session, query_input=query_input)
    except InvalidArgument:
        raise
    print("Query text:", response.query_result.query_text)
    print("Detected intent:", response.query_result.intent.display_name)
    print("Detected intent confidence:", response.query_result.intent_detection_confidence)
    print("Fulfillment text:", response.query_result.fulfillment_text)


def main():

    dialogflow_settings = {'dialogflow_project_id': 'russianposttrackbot-yy9j', 'dialogflow_language_code': 'Ru-ru'}
    dialogflow_project_id = 'russianposttrackbot-yy9j'
    dialogflow_language_code = 'Ru-ru'
    session_id = 'current-user-id1'
    key_json = 'rp3.json'
    message_text = 'ты кто'
    event_name = 'event_no'

    dialogflow_init(key_json)
    # dialogflow_get(dialogflow_settings, session_id, message_text)
    dialogflow_send_event(dialogflow_settings, session_id, event_name)


if __name__ == '__main__':
    main()
