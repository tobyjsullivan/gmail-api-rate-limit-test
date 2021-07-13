# Gmail API Rate Limit Test

Measure how fast emails can be sent via the Gmail API.

## Prerequisites

1. Create a Google Cloud App in the console.
   - Set up for Internal use to allow restricted scopes.
2. Generate OAuth credentials
   - Instructions: https://developers.google.com/workspace/guides/create-credentials
   - Required scopes:
      - `https://www.googleapis.com/auth/gmail.readonly`
      - `https://www.googleapis.com/auth/gmail.send`
3. Create the file `credentials.json` with the required scopes.

## Install dependencies

```sh
pip3.7 install -r requirements.txt
```

## Running

```sh
$ FROM=youremail@domain.com python3.7 main.py
```

## Analyzing output

Output will be written to `send_log.csv`. 

The columns are:
* `PID` - the process ID for the run. This generally changes each run and is just used for debugging purposes. Running multiple instances is untested but presumably this would allow differentiation of records.
* `Trial` - A monotonically increasing value indicating how many email sends have been attempted. This value will increase between runs of the script.
* `Timestamp`
* `Status` - The HTTP status code received when the send was attempted. 200 indicates the message was sent successfully. Any other status indicates the message failed to send.
* `To Address` - The email address the test email was sent to.
* `Subject` - The subject of the test email.
* `Body` - The body of the test email.

Load the output CSV in your favourite spreadsheet tool to analyze how frequently messages can be sent before you get 409 responses indicating rate limiting.
