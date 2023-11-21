from twilio.rest import Client #pip3 install twilio

import os

# This python file/module is my first attempt at collecting code
# for accessing my web APIs / accounts.

# I will modify all code to use keys/tokens stored in my environment.

def send_twilio_message(body: str, dest :str="+17209613665"):
    print("Sending SMS message via Twilio")
    twilio_account_sid= os.environ.get("TWILIO_ACCOUNT_SID")
    twilio_auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

    print(f"Using Twillow act_sid/auth_token: {twilio_account_sid}/{twilio_auth_token}")

    client = Client(twilio_account_sid, twilio_auth_token)

    message = client.messages \
        .create(
            from_='+18667883991',
            body=body,
            to=dest
        )

    print(message.status)

def main():
    send_twilio_message("Dev testing message. ignore!")

if __name__ == '__main__':
    main()