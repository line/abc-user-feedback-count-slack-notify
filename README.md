# ABC User Feedback Count Notification
![](.README_images/ufb-slack-notify-main.png)
ABC User Feedback Count Notification provides functionality to send notifications to Slack regarding the number of user feedbacks collected via [ABC User Feedback](https://github.com/line/abc-user-feedback). 

This enables more efficient response to feedback collected from customers.  

**Screenshot**  

![](.README_images/slack-message-screenshot.png)

## Architecture
If you're using Github Actions, your configuration would look like this
![](.README_images/architecture.png)

## Usage


ABC User Feedback Count Notification can be used in various ways, such as with GitHub Actions, servers, or serverless services.  
Below is how you can use it with GitHub Actions.

1. Create a .github/workflows/run-handler.yml file in your GitHub repo.
2. Add the following code to the run-handler.yml file.  
   (To help you understand, a run-handler.yml file exists in that repository.)
3. Create `AUF_API_KEY`, `SLACK_WEBHOOK_URL` secret using [GitHub Action's Secret](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions#creating-encrypted-secrets-for-a-repository).  
You can [generate a Slack incoming webhook token from here](https://api.slack.com/messaging/webhooks).

```yaml
name: Run Handler

on:
#  workflow_dispatch:
  schedule: # The settings in the github action are based on UTC.
    - cron: '*/1 * * * *'

jobs:
  run-script:
    runs-on: [ ubuntu-latest ]

    steps:
      - name: Check out the repository
        uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9.0'
  
      - name: Set environment variables
        run: |
          echo "AUF_SEARCH_API=https://{ABC UserFeedback Domain in use}/api/projects/{projectId}/channels/{channelId}/feedbacks/search" >> $GITHUB_ENV
          echo "AUF_URL=https://{ABC UserFeedback Domain in use}" >> $GITHUB_ENV
          echo "QUERY_SEARCH_TEXT_KEYS={ABC UserFeedback Search Feedbacks by Channel API query/searchText key}" >> $GITHUB_ENV
          echo "QUERY_SEARCH_TEXT_VALUES={ABC UserFeedback Search Feedbacks by Channel API query/searchText value}" >> $GITHUB_ENV
          echo "QUERY_SEARCH_INTERVAL_DAYS=1" >> $GITHUB_ENV
          echo "IGNORE_WHEN_NOTHING=false" >> $GITHUB_ENV

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r user-feedback-count-slack-notification/requirements.txt

      - name: Run Python script
        env:
          AUF_API_KEY: ${{ secrets.AUF_API_KEY }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: python user-feedback-count-slack-notification/run_handler.py
```


## Environment Variables
You can use the following environment variables to change Slack notifications.  
(AUF stands for ABC UserFeedback.)

| Environment                | Description                                                                                                                                                                                            | Required | Default Value | Example                                                                       |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:--------:|:-------------:|-------------------------------------------------------------------------------|
| AUF_SEARCH_API             | The URL endpoint of the ABC User Feedback API.<br/><br/> This is where the application sends requests to retrieve user feedback data.                                                                  |    O     |               | https://example.com/api/projects/16/channels/26/feedbacks/search              |
| AUF_API_KEY                | API key used to authenticate requests to the ABC UserFeedback API.<br/><br/>It can be obtained from your ABC UserFeedback settings.                                                                    |    O     |               |                                                                               |
| SLACK_WEBHOOK_URL          | The webhook URL for sending messages to a Slack channel.<br/><br/> This URL is used to post feedback notifications to Slack.                                                                           |    O     |               | https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX ||
| AUF_URL                    | Service The link to the URL of the ABC UserFeedback you are accessing.                                                                                                                                 |    X     |               | https://example.com                                                           |
| QUERY_SEARCH_TEXT_KEYS     | A comma-separated string of keys used in the feedback query.<br/><br/> These keys correspond to the fields in the feedback data that you want to filter by.                                            |    X     |               | categoryDepth1<br/>![](.README_images/description-query-search-text-keys.png) |
| QUERY_SEARCH_TEXT_VALUES   | A comma-separated string of values corresponding to `QUERY_SEARCH_TEXT_KEYS`.<br/><br/> Each value is used to filter the feedback data based on the corresponding key.                                 |    X     |               | error                                                                         |
| QUERY_SEARCH_INTERVAL_DAYS | An integer specifying the number of days to look back from today when querying feedback data.<br/><br/>  For example, setting it to `3` will query feedback data for the last 3 days, excluding today. |    X     |       1       | 1                                                                             |
| IGNORE_WHEN_NOTHING        | Sets whether to send a Slack notification if no feedback is registered for the period of time set in `QUERY_SEARCH_INTERVAL_DAYS`. `true` : Do not send notifications, `false` : Send notifications    |    X     |     false     | true                                                                          |

Below screenshot help you visualize message part controlled by different variables:
![](.README_images/description-slack-message-content.png)

## License

```
Copyright 2024 LY Corporation

LY Corporation licenses this file to you under the Apache License,
version 2.0 (the "License"); you may not use this file except in compliance
with the License. You may obtain a copy of the License at:

  https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
```
