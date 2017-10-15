# Ringo Slackbot

A slackbot for interacting with Spotify in the office for democratising the playback!

<img src="/screenshot/ringo_starr.jpg" width="300" alt="Ringo Starr" />



## Development

### Backgorund


### Installation

In order to run the project locally you will need to clone/fork the repository. In addition please follow the guide below for getting the slack bot up and running.

If you have any questions or problems with the following guide please submit an issue: https://github.com/globalmouth/ringo/issues

1. Clone or fork the repository and cd into the directory

2. Ensure you have **python 3.x** installed on your machine. You can check your version with the following command:  `python --version`. If you do not have python installed please follow the guide relevent to your OS http://docs.python-guide.org/en/latest/starting/installation/#installation-guides

3. It is recommended to run the project from within a virtual environment. To ensure you have this setup please follow the guide to setting it up http://docs.python-guide.org/en/latest/dev/virtualenvs/#lower-level-virtualenv


Once you have succeeded with the above lets get the project running.

```bash
# inside the ringo directory /ringo

# create a venv folder for installing dependencies and environment 
$ virtualenv venv

# activate the virtual environment
$ source venv/bin/activate

# install all requirements for the project
$ pip install -r requirements.txt

# starting the bot is done with
$ rtmbot
```