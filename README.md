# secret-santa
A fun little secret Santa project I was doing last year

Create a config.py file with the following variables: 
* mailServer = ''; what mail server to connect to 
* fromAddress = ''; the account to connect to the mail server with and send email from 
* mailPassword = ''; the password of the account to connect to the mail server
* family = 'testing1'; the name of the family to generate results for
* participants = [{'Name': '', 'Email': ''}]; who to include in the process
* spouses = {'': ''};  pairs of married people
* sendEmail = False; whether we should send an email or not
* priorYearsFileNames = ['']; the prior year file names to look at for processing

Example:

```
mailPassword = 'Password'
mailServer = 'smtp.somewhere.com'
fromAddress = 'reply@example.com'
family = 'testing1'
participants = [
    {'Name': 'Nobody', 'Email': 'nobody@example.com'},
    {'Name': 'Someone', 'Email': 'someone@example.com'},
    {'Name': 'Who', 'Email': 'who@example.com'},
    {'Name': 'What', 'Email': 'what@example.com'}
]
spouses = {'Someone': 'Who'}
sendEmail = False
priorYearsFileNames = ['testing.json']
```

Then run the main.py file
`python3 main.py`