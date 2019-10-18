# Kudos

Application to run the Kudos Awards for Scotch'n'Soda Theatre at Carnegie Mellon University using Heroku.

# Flask Config

There are several attributes defined in the top-level `config.py` file. The only attributes you may need to change are the email ones. It is setup by default to handle Google Mail, so any gmail or G Suite (like CMU andrew emails) should work fine by default and not require changes, but if you use a different mail provider then you should look up the appropriate attributes to use for Flask Mail for your email service.

You will need to create a file named `config_secrets.py` in the top level directory with the following attributes defined:

```python
key = "your-secret-key"
email = "yourusername@gmail.com"
password = "yourpassword"
```

To generate a secret key, it suffices to use the `secrets.token_urlsafe` function from python's [secrets](https://docs.python.org/3/library/secrets.html#secrets.token_urlsafe "secrets") library.

# Google Mail

If you would like to use Gmail to send emails, you will need to take a few steps to get authentication working properly.

Gmail has some strict security protocols that this flask app cannot adhere to, so you will need to turn on the setting to allow "less secure apps" to access your account. Alternatively, if your account has 2 Factor Authentication turned on, you will need to generate an app password and use that in place of your account password above. This will not require the "less secure apps" setting.

Additionally, you may also use whatever G Suite domain you have for Google Mail. For example, CMU students may use your @andrew.cmu.edu email. To set this up, follow the instructions at [this page](https://www.cmu.edu/computing/services/comm-collab/email-calendar/google/how-to/index.html "this page") titled "How to Use Google Mail" in the section about setting up an email client and set a G Suite password, which you will use as the password in the config secrets file. This might require the "less secure apps" setting mentioned above.

# Local Testing

Before deploying the application, you should test it locally to make sure everything works. First, clone this git repository to somewhere on your machine, install the requirements, create and fill `config_secrets.py`, run the `init_db` function from `init_db.py`, and then run `application.py`. Then open the url given in the console and try to create an account and submit some nominations. You can return to `init_db.py` and run the `give_admin` function on your username to make yourself an admin, and then explore the admin page which should now appear in the dropdown menu under your username on the site.

# Heroku Setup

This application is configured to run with Heroku, which handles deployment of the app. It lets you run limited applications for free, but the paid tier is [really cheap](https://www.heroku.com/pricing "really cheap") (especially if you're only running it for 2 weeks). The main benefit of the Hobby plan is getting a custom domain with SSL security (so it can be hosted at kudos.snstheatre.org, for example), and not having the app fall asleep after 30 minutes.

To get started, set up a Heroku account and download the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli "Heroku CLI"). Then open a console or command prompt on your computer and cd over to the repository folder. From there, run the following command, selecting a universally unique name for your application:

```
heroku create sns-kudos
```

Then add a database to the application:

```
heroku addons:create heroku-postgresql:hobby-dev
```

When that completes, take note of the herokuapp url it gives you. This is where your application will be hosted (at least for now). Then, run

```
python config_heroku.py
```

This sets the environment variables from your `config_secrets.py` file on the heroku server. Then, run

```
git push heroku master
```

This will deploy the application. Once that completes, you need to initialize the database on the heroku server. To do that, run

```
heroku run python
```

When the python console opens, run the following commands:

```python
>>> from init_db import init_db
>>> init_db()
>>> quit()
```

Then, head over to the herokuapp url mentioned above, and make sure everything works fine. Like before, test creating an account and submitting nominations. Sometimes there are security issues with sending emails once the app has been deployed, so make sure email sending functions work (like when you create an account), and fix any problems if they arise. Then, like before, make yourself an admin by running

```python
>>> from init_db import give_admin
>>> give_admin("yourusername")
>>> quit()
```

Alternatively, you can make an admin account for yourself at the same time you initialize the database by importing and running `init_user_admin("username")`. The password of an account created this way will be "password" but this can be changed from the website.

# Extra Heroku Stuff

Now the application should be fully running on Heroku's free plan. If you want to take advantage of the paid plan, you can do so by logging into your heroku account online and changing the settings in your app to use a paid dyno. Then you can also set up a custom domain.

Note: you can use custom domains on free dynos, but those won't have SSL certificates, so https won't work, and since this application handles passwords you should always make sure https works.

# Not from CMU?

You can modify this application to support non cmu email addresses. If your organization uses a different unified email domain, you can simply change the `default_email` function in `models.py` to use your domain instead of the andrew.cmu.edu domain. To support arbitrary emails, you could either add an email field to the account signup form, or go through the whole application and combine the username and email attributes into one (i.e. make it so that the username is their email). For the former, you should also look into the password recovery page and add an option for submitting your email in case they forgot their username. In any case, you should change the form titles that currently say "Andrew ID" to whatever method you choose.
