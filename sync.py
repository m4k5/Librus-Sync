import json
import os.path
import pickle
from datetime import datetime, timedelta
from getpass import getpass

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from librus_tricks import utilities, aio, SynergiaClient

SCOPES = ['https://www.googleapis.com/auth/calendar']
google_calendar_pickle_path = '.data/googlecalendar.pickle'
synergia_pickle_path = '.data/synergiasession.pickle'
local_data_path = '.data/data.json'


def ask_librus_creds():
    return {
        'email': input('Email: '),
        'passwd': getpass()
    }


class AppData:
    def __init__(self):
        if os.path.exists(local_data_path):
            with open(local_data_path, 'r') as file:
                self.data = json.load(file)
        else:
            with open(local_data_path, 'w') as file:
                self.data = dict()
                self.data['uploaded_exams'] = []
                self.data['notify_time'] = '17:45'
                json.dump(self.data, file)

    def update(self):
        with open(local_data_path, 'w') as file:
            json.dump(self.data, file)


class SynergiaImproved:
    def __init__(self):
        self.session = None
        if os.path.exists(synergia_pickle_path):
            with open(synergia_pickle_path, 'rb') as pickle_file:
                self.session = SynergiaClient(pickle.load(pickle_file))

        if not os.path.exists(synergia_pickle_path):
            self.session = SynergiaClient(aio(**ask_librus_creds()))
            with open(synergia_pickle_path, 'wb') as pickle_file:
                pickle.dump(self.session.user, pickle_file)
        elif not self.session.user.is_authenticated:
            self.session = SynergiaClient(aio(**ask_librus_creds()))
            with open(synergia_pickle_path, 'wb') as pickle_file:
                pickle.dump(self.session.user, pickle_file)


class GoogleCalendar:
    def __init__(self):
        credentials = None
        if os.path.exists(google_calendar_pickle_path):
            with open(google_calendar_pickle_path, 'rb') as token:
                credentials = pickle.load(token)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                credentials = flow.run_local_server()
            with open(google_calendar_pickle_path, 'wb') as token:
                pickle.dump(credentials, token)

        self.service = build('calendar', 'v3', credentials=credentials)


class Synchronizer:
    def __init__(self, google_calendar, synergia_session, storage_manager):
        """

        :param GoogleCalendar google_calendar:
        :param librus_tricks.SynergiaClient synergia_session:
        :param AppData storage_manager:
        """
        self.calendar = google_calendar.service
        self.syn_session = synergia_session
        self.storage = storage_manager

    def upload_exams(self):
        print('Downloading exams...')
        exams = self.syn_session.get_future_exams()
        print('Exams downloaded')
        for exam in exams:
            print(exam)
            if exam.oid not in storage.data['uploaded_exams']:
                if exam.time_start is None and exam.time_end is None:
                    tt = self.syn_session.get_timetable(
                        week_start=utilities.get_first_day_of_week(exam.date).strftime('%Y-%m-%d')
                    )
                    tmp_var__start = tt[exam.date.strftime('%Y-%m-%d')][int(exam.lesson) - 1].start
                    tmp_var__end = tt[exam.date.strftime('%Y-%m-%d')][int(exam.lesson) - 1].end
                    start = datetime(
                        year=exam.date.year,
                        month=exam.date.month,
                        day=exam.date.day,
                        hour=tmp_var__start.hour,
                        minute=tmp_var__start.minute,
                        second=tmp_var__start.second,
                    )
                    end = datetime(
                        year=exam.date.year,
                        month=exam.date.month,
                        day=exam.date.day,
                        hour=tmp_var__end.hour,
                        minute=tmp_var__end.minute,
                        second=tmp_var__end.second,
                    )
                else:
                    tmp_var__start = exam.time_start
                    tmp_var__end = exam.time_end
                    start = datetime(
                        year=exam.date.year,
                        month=exam.date.month,
                        day=exam.date.day,
                        hour=tmp_var__start.hour,
                        minute=tmp_var__start.minute,
                        second=tmp_var__start.second,
                    )
                    end = datetime(
                        year=exam.date.year,
                        month=exam.date.month,
                        day=exam.date.day,
                        hour=tmp_var__end.hour,
                        minute=tmp_var__end.minute,
                        second=tmp_var__end.second,
                    )

                hour_notification = datetime.strptime(storage.data['notify_time'], '%H:%M')
                datetime_exam = datetime(
                    year=exam.date.year,
                    month=exam.date.month,
                    day=exam.date.day,
                    hour=start.hour,
                    minute=start.minute
                )
                day_before = exam.date - timedelta(days=1)
                notification_datetime = datetime(
                    year=day_before.year,
                    month=day_before.month,
                    day=day_before.day,
                    hour=hour_notification.hour,
                    minute=hour_notification.minute
                )

                google_calendar_payload = {
                    'summary': f'{exam.category.name} z {exam.subject.name}',
                    'description': f'"{exam.content}" wpisane przez {exam.teacher.name} {exam.teacher.last_name} o {exam.add_date.isoformat()}',
                    'start': {
                        'dateTime': f'{start.isoformat()}',
                        'timeZone': f'Europe/Warsaw'
                    },
                    'end': {
                        'dateTime': f'{end.isoformat()}',
                        'timeZone': f'Europe/Warsaw'
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': (datetime_exam - notification_datetime).seconds // 60}
                        ]
                    }
                }
                self.calendar.events().insert(calendarId='primary', body=google_calendar_payload).execute()
                self.storage.data['uploaded_exams'].append(
                    exam.oid
                )
            else:
                print('Skipping...')


if __name__ == '__main__':
    print('Creating storage')
    storage = AppData()
    print('Creating Librus Synergia session')
    synergia = SynergiaImproved().session
    print('Creating Google Calendar session')
    google_cal = GoogleCalendar()
    print('Creating Synchronizer')
    sc = Synchronizer(
        google_cal, synergia, storage
    )
    sc.upload_exams()
    storage.update()
