from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from quickstart import get_credentials
import datetime

from os.path import isfile
import pickle
import pytz
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def pandas_holidays():
    from pandas.tseries.holiday import USFederalHolidayCalendar
    cal = USFederalHolidayCalendar()
    holidays = cal.holidays(start='2014-01-01', end='2014-12-31').to_pydatetime()
    if datetime.datetime(2014,1,1) in holidays:
        print(True)

def events_in_interval(interval_start, interval_end, cal_ID):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    eventsResult = service.events().list(
        calendarId=cal_ID,
        timeMin=interval_start.isoformat() + 'Z',
        timeMax=interval_end.isoformat() + 'Z',
        maxResults=1000,
        singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    return events

def events_per_interval(search_start, search_end, interval = 7, cal_ID = 'primary'):
    events = events_in_interval(search_start, search_end, cal_ID)
    events_per_interval = []
    interval_start = search_start
    interval_end = search_start + datetime.timedelta(days=0.9999*interval)
    labels = []
    num_events = 0
    for event in events:
        # import pdb
        # pdb.set_trace()
        try:
            start_str = event['start']['dateTime'][0:10]
        except:
            start_str = event['start']['date']
        start = datetime.datetime.strptime(start_str, '%Y-%m-%d')
        while interval_end < start:
            line = [interval_start, interval_end, num_events, labels]
            # slide to the interval the events start in, creating null lines along the way
            print(line)
            events_per_interval.append(line)
            # set variables for next interval
            interval_start = interval_start + datetime.timedelta(days=interval)
            interval_end = interval_end + datetime.timedelta(days=interval)
            num_events = 0
            labels = []
        # do the stuff to count the interval
        labels.append(event['summary'])
        num_events += 1
    return pd.DataFrame(events_per_interval, columns = ['start', 'end', 'num_Events', 'events'])

def events_created_per_interval(search_start, search_end, interval = 7, cal_ID = 'primary'):
    # plus average lead time over intervals
    events = events_in_interval(search_start, search_end, cal_ID)
    events_per_interval = []
    leads = []
    interval_start = search_start
    interval_end = search_start + datetime.timedelta(days=0.9999*interval)
    labels = []
    num_events = 0
    for event in events:
        created_str = event['created'][0:10]
        created = datetime.datetime.strptime(created_str, '%Y-%m-%d')
        try:
            start_str = event['start']['dateTime'][0:10]
        except:
            start_str = event['start']['date']
        start = datetime.datetime.strptime(start_str, '%Y-%m-%d')
        leads.append((start - created).days)
        while interval_end < created:
            if len(leads) > 0:
                avg_lead = sum(leads)/len(leads)
            else:
                avg_lead = 0
            line = [interval_start, interval_end, num_events, avg_lead, labels]
            # slide to the interval the events start in, creating null lines along the way
            events_per_interval.append(line)
            # set variables for next interval
            interval_start = interval_start + datetime.timedelta(days=interval)
            interval_end = interval_end + datetime.timedelta(days=interval)
            num_events = 0
            labels = []
            leads = []
        # do the stuff to count the interval
        labels.append(event['summary'])
        num_events += 1
    # avg_lead = sum(leads)/len(leads)
    return pd.DataFrame(events_per_interval, columns = ['start', 'end', 'num_Events', 'avg_Lead', 'events'])

if __name__ == '__main__':
    # main()
    today = datetime.datetime.now().date()
    now = datetime.datetime.now()
    midnight = datetime.datetime.combine(today, datetime.time(0, 0))
    # search_end = midnight.astimezone(pytz.utc)
    search_start = (midnight - datetime.timedelta(days=600))
    if isfile('holidays.pkl') and (input("Load holiday data from file?")=='y'):
        holidays = pickle.load(open('holidays.pkl', 'rb'))
    else:
        holidays = events_in_interval(
                        interval_start = search_start,
                        interval_end = midnight,
                        cal_ID = 'en.usa#holiday@group.v.calendar.google.com')
        pickle.dump(holidays, open('holidays.pkl', 'wb'))
    ignore_list = {'Election Day', 'Daylight Saving Time ends', 'Daylight Saving Time starts', 'Christmas Eve', 'Christmas Day observed', 'New Year\'s Eve', 'New Year\'s Day observed', "Thomas Jefferson's Birthday"}
    # finish this list to ignore the holidays getting in the way.
    h_plot_data = [[holiday['start']['date'], 1, holiday['summary']] for holiday in holidays if holiday['summary'] not in ignore_list]
    dates = mpl.dates.datestr2num([h[0] for h in h_plot_data])
    values = [h[1] for h in h_plot_data]
    cal_ID = 'hbe4hm8eu1r0v6ohp9kofi331k@group.calendar.google.com'
    # events = events_in_interval(search_start, midnight+datetime.timedelta(days=365), cal_ID)
    if isfile('events.pkl') and (input("Load event data from file?")=='y'):
        weekly_events, created_per_week = pickle.load(open('events.pkl', 'rb'))
    else:
        weekly_events = events_per_interval(search_start, midnight, 7, cal_ID)
        created_per_week = events_created_per_interval(search_start, midnight, 7, cal_ID)
        pickle.dump([weekly_events, created_per_week], open('events.pkl', 'wb'))
    avg_lead = created_per_week['avg_Lead'].mean()
    print("Average lead time is ", avg_lead)
    # daily_events = events_per_interval(search_start, interval=1)
    # biweekly_events = events_per_interval(interval=14)
    # monthly_events = ....
    # quarterly_events = ....
    labels = [h[2] for h in h_plot_data]
    # fig = plt.figure(figsize=(15, 3.5))
    # # plt.subplots_adjust(bottom = 0.1)
    # plt.scatter(dates, values, marker='|')
    #
    # for label, x, y in zip(labels, dates, values):
    #     plt.annotate(
    #         label,
    #         xy=(x, y), xytext=(10, 5), fontsize=6, rotation=80,
    #         textcoords='offset points', ha='right', va='bottom',
    #         bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.3))
    #         # arrowprops=dict(arrowstyle = '->', connectionstyle='arc3,rad=0'))
    #
    # capacity = weekly_events['num_Events'].max()
    # plt.plot(weekly_events['start'], weekly_events['num_Events'], label="Weekly Events")
    # plt.plot(created_per_week['start'], created_per_week['num_Events'], label="Created Events")
    # plt.gca().set_ylabel('Weekly Events')
    # title_str = "Events per Week and Events Created per Week \n Average Lead Time on Events: " + str(int(avg_lead)) + " days"
    # plt.title(title_str)
    # plt.xticks(list(weekly_events['start']),
    #     [str(w.month)+"-"+str(w.day) for w in weekly_events['start']],  rotation=70)
    # plt.legend()
    # plt.tight_layout()
    # plt.show()
    # plt.close('all')

    fig = plt.figure(figsize=(15, 3.5))
    # plt.subplots_adjust(bottom = 0.1)
    plt.scatter(dates, values, marker='|')

    for label, x, y in zip(labels, dates, values):
        plt.annotate(
            label,
            xy=(x, y), xytext=(10, 5), fontsize=6, rotation=80,
            textcoords='offset points', ha='right', va='bottom',
            bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.3))
            # arrowprops=dict(arrowstyle = '->', connectionstyle='arc3,rad=0'))

    plt.plot(created_per_week['start'], created_per_week['avg_Lead'], label="Weekly Average Lead")
    plt.xticks(list(weekly_events['start']),
        [str(w.month)+"-"+str(w.day) for w in weekly_events['start']],  rotation=70)
    plt.legend()
    plt.tight_layout()
    plt.show()
    plt.close('all')
