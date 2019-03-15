import subprocess
from config_secrets import key, email, password

subprocess.run(["heroku", "config:set",
    "SECRET_KEY=" + key,
    "MAIL_USERNAME=" + email,
    "MAIL_PASSWORD=" + password],
    shell=True)
