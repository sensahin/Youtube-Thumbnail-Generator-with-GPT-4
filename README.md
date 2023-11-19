
#Setup

python3 -m venv env

source env/bin/activate

pip install -r requirements.txt

# AWS setup

- Create your bucket here: https://s3.console.aws.amazon.com/s3/
- Create your access key here: https://us-east-1.console.aws.amazon.com/iam/home#/security_credentials
- Paste them in app.py line 17,18,19

# Usage

python3 app.py