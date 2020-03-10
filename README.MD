# NEC ITSM incidents notfier

This project aims to provide telegram notifications for incidents emailed to the configured email address.


Requires Gmail API in order to work. As such, follow the guide [here](https://developers.google.com/gmail/api/quickstart/python) to authorize email to work with the project.


On first run, follow the link in the console output to authorize the email address.

Create `config.py` in the root folder of the project with the following code:

```python
class Config:
    token = 'API_token_key' #telegram bot token
    chat_id = '123456789' #telegram chat id to send to
    sender_email = 'test@gmail.com' #only watch emails from this email address
    sleep_time = 300 #time in seconds to wait between each run of program
```

Example of config is in `config.sample.py`