# Copyright 2024 LY Corporation
#
# LY Corporation licenses this file to you under the Apache License,
# version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at:
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import re
from datetime import datetime, timedelta

import pytz
import requests

AUF_SEARCH_API = os.environ.get('AUF_SEARCH_API')
AUF_API_KEY = os.environ.get('AUF_API_KEY')
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
AUF_URL = os.environ.get('AUF_URL', '')
QUERY_SEARCH_TEXT_KEYS = os.environ.get('QUERY_SEARCH_TEXT_KEYS', '')
QUERY_SEARCH_TEXT_VALUES = os.environ.get('QUERY_SEARCH_TEXT_VALUES', '')
QUERY_SEARCH_INTERVAL_DAYS = int(os.environ.get('QUERY_SEARCH_INTERVAL_DAYS', '1'))
IGNORE_WHEN_NOTHING = os.environ.get('IGNORE_WHEN_NOTHING', 'false')

TIMEZONE = 'Asia/Tokyo'
AUF_API_HEADERS = {
    "x-api-key": AUF_API_KEY,
    "Content-Type": "application/json"
}


def handler(event, context):
    global TIMEZONE
    project_info_response = get_project_info()
    project_name = project_info_response.json()['name']
    timezone_name = project_info_response.json().get('timezone', {}).get('name')
    if timezone_name:
        TIMEZONE = timezone_name
    query_response = query_abc_user_feedback() if QUERY_SEARCH_TEXT_KEYS and QUERY_SEARCH_TEXT_VALUES else None
    total_response = total_abc_user_feedback()

    total_data_count = 0
    message, total_data_count = generate_message(project_name,
                                                 query_response,
                                                 total_data_count,
                                                 total_response)

    if (project_info_response.status_code == 200 and
            query_response.status_code == 201 and
            total_response.status_code == 201 and
            total_data_count == 0 and
            IGNORE_WHEN_NOTHING == 'true'
    ):
        return {
            'query_response_status_code': query_response.status_code,
            'total_response_status_code': total_response.status_code,
            'send_slack_message_status_code': 'No registered feedback.'
        }

    send_slack_message_response = send_slack_message(message)

    return {
        'project_info_response_status_code': project_info_response.status_code,
        'query_response_status_code': query_response.status_code,
        'total_response_status_code': total_response.status_code,
        'send_slack_message_status_code': send_slack_message_response.status_code
    }


def get_project_info():
    global get_project_info_url
    match = re.search(r'(https://[^/]+(?:/[^/]+)*/projects/\d+)', AUF_SEARCH_API)

    if match:
        get_project_info_url = match.group(1)
        print("Project URL:", get_project_info_url)
    else:
        print("Project URL not found")

    return requests.get(get_project_info_url, headers=AUF_API_HEADERS)


def query_abc_user_feedback():
    data = {
        "limit": 10,
        "page": 1,
        "query": build_query()
    }
    return requests.post(AUF_SEARCH_API, headers=AUF_API_HEADERS, json=data)


def build_query():
    start_utc_str, end_utc_str = get_utc_date_range()
    query = {
        "createdAt": {
            "gte": start_utc_str,
            "lt": end_utc_str
        }
    }
    if QUERY_SEARCH_TEXT_KEYS and QUERY_SEARCH_TEXT_VALUES:
        keys = QUERY_SEARCH_TEXT_KEYS.split(',')
        values = QUERY_SEARCH_TEXT_VALUES.split(',')
        if len(keys) == len(values):
            query.update({key.strip(): value.strip() for key, value in zip(keys, values)})
    return query


def total_abc_user_feedback():
    start_utc_str, end_utc_str = get_utc_date_range()
    data = {
        "limit": 10,
        "page": 1,
        "query": {
            "createdAt": {
                "gte": start_utc_str,
                "lt": end_utc_str
            }
        }
    }
    response = requests.post(AUF_SEARCH_API, headers=AUF_API_HEADERS, json=data)
    return response


def send_slack_message(message):
    data = {
        "text": message
    }
    response = requests.post(SLACK_WEBHOOK_URL, headers={"Content-Type": "application/json"}, json=data)
    return response


def get_utc_date_range():
    local_tz = pytz.timezone(TIMEZONE)

    start_day = datetime.now(local_tz) - timedelta(days=QUERY_SEARCH_INTERVAL_DAYS)
    start_of_day_local = local_tz.localize(datetime(start_day.year, start_day.month, start_day.day, 0, 0, 0))
    end_of_day_local = start_of_day_local + timedelta(days=QUERY_SEARCH_INTERVAL_DAYS) - timedelta(microseconds=1)

    start_of_day_utc = start_of_day_local.astimezone(pytz.utc)
    end_of_day_utc = end_of_day_local.astimezone(pytz.utc)

    start_utc_str = start_of_day_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    end_utc_str = end_of_day_utc.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    return start_utc_str, end_utc_str


def generate_message(project_name, query_response, total_data_count, total_response):
    abc_user_feedback_client_name = f"[{project_name}]"
    abc_user_feedback_link = f"Here is a link to <{AUF_URL}|ABC UserFeedback>" if AUF_URL else ""

    if query_response and query_response.status_code == 201 and total_response.status_code == 201:
        query_data_count = query_response.json()['meta']['totalItems']
        total_data_count = total_response.json()['meta']['totalItems']
        message = (
            f"{abc_user_feedback_client_name} New feedback registered (For {QUERY_SEARCH_INTERVAL_DAYS} days) \n"
            f" • {QUERY_SEARCH_TEXT_VALUES} : {query_data_count} \n"
            f" • total : {total_data_count} \n"
            f"{abc_user_feedback_link}"
        )
    else:
        message = (
            f"Failure: Query Count ABC UserFeedback API call response status code : {query_response.status_code}, \n "
            f" Total Count ABC UserFeedback API call response status code : {total_response.status_code}")
    return message, total_data_count
