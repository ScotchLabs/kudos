# Kudos
Application to run the Kudos Awards for Scotch'n'Soda Theatre at Carnegie Mellon University

# Flask Config
Specify the following attributes in top-level `config.py`:

```python
DEBUG = False # should be False in production
SQLALCHEMY_DATABASE_URI
SECRET_KEY
BCRYPT_LOG_ROUNDS = 12 # usually a good bet
SQLALCHEMY_TRACK_MODIFICATIONS = False # to silence a flask warning
MAIL_SERVER # the setup of these may vary based based on which email you use
MAIL_PORT
MAIL_USE_SSL
MAIL_USERNAME
MAIL_PASSWORD
MAIL_DEFAULT_SENDER = MAIL_USERNAME # unless you want to specify otherwise
REMEMBER_COOKIE_DURATION = 604800 # 1 week in seconds, for flask-login
BASIC_AUTH_USERNAME
BASIC_AUTH_PASSWORD
```

# Google Mail

If you would like to use Gmail to send emails, these flask-mail settings work:

```python
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = "yourusername@gmail.com"
MAIL_PASSWORD = "yourpassword"
```

Note that Gmail has some strict security protocols that this flask app cannot adhere to, so you will need to turn on the setting to allow "less secure apps" to access your account. Alternatively, if your account has 2 Factor Authentication turned on, you will need to generate an app password and use that in place of your account password above. This will not require the "less secure apps" setting.

Additionally, you may also use whatever GSuite domain you have for Google Mail in place of the @gmail.com above. For example, CMU students may use your @andrew.cmu.edu email. To set this up, google "cmu how to use google mail" and set a G Suite password, which you will use as the `MAIL_PASSWORD` above. This also does not require the "less secure apps" setting.

# EB Config

To run this application on AWS Elastic Beanstalk, you must create some config files in the directory `.ebextensions/`:

`.ebextensions/securelistener-clb.config` (assuming https support, using a certificate on ACM)
```
option_settings:
  aws:elb:listener:443:
    SSLCertificateId: arn:aws:acm:us-east-2:1234567890123:certificate/####################################
    ListenerProtocol: HTTPS
    InstancePort: 80
```

`.ebextensions/auth.config` (send flask basic auth credentials as plain text)
```
container_commands:
  01_wsgi_pass_headers:
    command: 'echo "WSGIPassAuthorization On" >> ../wsgi.conf'
```

If using the EB CLI, you will also need to at least create an empty `.ebignore` file, otherwise `.gitignore` will be used by default, which will ignore your `config.py` file. You may of course also add to this file whatever else you want to ignore.
