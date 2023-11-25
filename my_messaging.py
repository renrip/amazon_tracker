from twilio.rest import Client #pip3 install twilio
import smtplib

import os

# This python file/module is my first attempt at collecting code
# for accessing my web APIs / accounts.

# I will modify all code to use keys/tokens stored in my environment.

def send_twilio_message(body: str, dest :str="+17209613665"):
    print("Sending SMS message via Twilio")
    twilio_account_sid= os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    # TODO fix cron setup so that it will see my ENV vars from .bashrc
    print(f"Using Twillow act_sid/auth_token: {twilio_account_sid}/{twilio_auth_token}")

    client = Client(twilio_account_sid, twilio_auth_token)

    message = client.messages \
        .create(
            from_='+18667883991',
            body=body,
            to=dest
        )

    print(message.status)

def send_gmail_message(subject :str, message: str, to: str = "craig@pirner.org"):
        print("Sending email message via Gmail (SMTP)")

        # TODO sanity check inputs. Wrap in a try? or let caller do that?

        gmail_user = os.environ.get("GMAIL_USER")
        gmail_password =  os.environ.get("GMAIL_APP_PASSWORD") # Special app password created in gmail for this

        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=gmail_user, password=gmail_password)
            connection.sendmail(from_addr=gmail_user, 
                                to_addrs=to, 
                                msg="Subject:" + subject + "\n\n" + message)
    

def main():
    print("Entering: my_messaging.py main()")

    # Un comment these to test the method.
    # Leaving them commented to avoid accidental messaging.

    # send_twilio_message("Dev testing message. ignore!")
    # send_gmail_message("Test msg from Python", "This is the body of the test message.\nLine #2", "craig@pirner.org")

if __name__ == '__main__':
    main()