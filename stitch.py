import os
import jwt
import time
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()


def generate_client_assertion():
    with open(os.getenv("STITCH_CERT_PATH"), "r") as cert:
        secret = cert.read()
    now = int(time.time())
    one_hour_from_now = now + 3600000

    payload = {
        "aud": "https://secure.stitch.money/connect/token",
        "iss": os.getenv("STITCH_CLIENT_ID"),
        "sub": os.getenv("STITCH_CLIENT_ID"),
        "jti": str(uuid.uuid4()),
        "iat": now,
        "nbf": now,
        "exp": one_hour_from_now
    }
    encoded_jwt = jwt.encode(payload, secret, algorithm="RS256")

    return encoded_jwt


def generate_client_token():
    encoded_jwt = generate_client_assertion()
    data = {
        "grant_type": "client_credentials",
        "client_id": os.getenv("STITCH_CLIENT_ID"),
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "audience": "https://secure.stitch.money/connect/token",
        "scope": "client_paymentrequest",
        "client_assertion": encoded_jwt,
    }
    r = requests.post("https://secure.stitch.money/connect/token", data=data)
    return r.json()


def generate_pay_page(amount=1000, bank_id="united_bank_for_africa", account_number="1234567890", name="Test", reference="Test"):
    query = """mutation MyMutation {
  __typename
  clientPaymentInitiationRequestCreate(input: {amount: {quantity: "%s", currency: "NGN"}, beneficiary: {bankAccount: {bankId: %s, accountNumber: "%s", name: "%s"}}, payerReference: "%s", beneficiaryReference: "%s"}) {
    paymentInitiationRequest {
      id
      url
    }
  }
}""" % (amount, bank_id, account_number, name, reference, reference)
    headers = {
        "Authorization": f"Bearer {generate_client_token()['access_token']}"
    }
    r = requests.post("https://api.stitch.money/graphql",
                      json={"query": query}, headers=headers)
    payment_url = r.json()[
        "data"]["clientPaymentInitiationRequestCreate"]["paymentInitiationRequest"]["url"]
    return f"{payment_url}?redirect_uri={os.getenv('STITCH_REDIRECT_URL')}"
