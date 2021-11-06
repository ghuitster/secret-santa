from random import shuffle
from flask import Flask, request
import ast
import json
import os.path
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config

app = Flask(__name__)

superSecretPassword = config.secretPassword

def doesAGiverHaveThemself(givers, receivers):
	for i, giver in enumerate(givers):
		if giver == receivers[i]:
			return True

	return False

def doesAGiverHaveTheirSpouse(givers, receivers, spouseMapping):
	inverseSpouseMapping = {value: key for key, value in spouseMapping.items()}

	for i, receiver in enumerate(receivers):
		if spouseMapping.get(givers[i]) == receiver:
			return True

		if inverseSpouseMapping.get(givers[i]) == receiver:
			return True

	return False

def getPriorYearReceiver(giver, priorYear):
	for giverEntry in priorYear['results']:
		if giverEntry['Name'] == giver:
			return giverEntry['Receiver']

	return None

def doesAGiverHaveWhoTheyHadLastYear(givers, receivers, priorYear):
	print(priorYear)
	for i, giver in enumerate(givers):
		if getPriorYearReceiver(giver, priorYear) == receivers[i]:
			return True

	return False

def isResultValid(givers, receivers, spouseMapping, priorYear):
	return not doesAGiverHaveThemself(givers, receivers) and not (spouseMapping and doesAGiverHaveTheirSpouse(givers, receivers, spouseMapping)) and not (priorYear and doesAGiverHaveWhoTheyHadLastYear(givers, receivers, priorYear))

def createResult(giverNames, giverEmails, receivers):
	results = []

	if request.json['sendEmail']:
		for i, giver in enumerate(giverNames):
			results.append({'Name': giver, 'Email': giverEmails[giver], 'Receiver': receivers[i]})
	else:
		for i, giver in enumerate(giverNames):
			results.append({'Name': giver, 'Receiver': receivers[i]})

	return results

def shuffleReceiversUntilValid(givers, receivers, spouseMapping, priorYear):
	while not isResultValid(givers, receivers, spouseMapping, priorYear):
		shuffle(receivers, random.SystemRandom().random)

def thereIsAValidResult(givers, spouseMapping):
	return len(givers) > 1 and (not spouseMapping or len(givers) > 3)

def everySpouseIsAParticipant(givers, spouseMapping):
	for key, value in spouseMapping.items():
		if key not in givers or value not in givers:
			return False

	return True

def everySpouseIsMarriedToSomeoneElse(spouseMapping):
	for key, value in spouseMapping.items():
		if key == value:
			return False

	return True

def thereAreNoDuplicateParticipants(givers):
	return len(givers) == len(set(givers))

def everySpouseIsMarriedToOnePerson(spouseMapping):
	keys = list(spouseMapping.keys())
	values = list(spouseMapping.values())

	for key in keys:
		if key in values:
			return False

	for value in values:
		if value in keys:
			return False

	return len(keys) == len(set(keys)) and len(values) == len(set(values))

def spouseMappingIsValid(givers, spouseMapping):
	if not spouseMapping:
		return True

	return everySpouseIsAParticipant(givers, spouseMapping) and everySpouseIsMarriedToSomeoneElse(spouseMapping) and everySpouseIsMarriedToOnePerson(spouseMapping)

def extractGiverNames(participants):
	giverNames = []

	for participant in participants:
		giverNames.append(participant['Name'])

	return giverNames

def extractGiverEmails(participants):
	if not request.json['sendEmail']:
		return None

	giverEmails = {}

	for participant in participants:
		giverEmails[participant['Name']] = participant['Email']

	return giverEmails

def emailResults(family):
	with open(family + '.json', 'r') as resultsFile:
		participantPairs = json.load(resultsFile)['results']

	server = smtplib.SMTP_SSL(config.mailServer, 465)
	server.ehlo()
	sentFrom = config.fromAddress
	server.login(sentFrom, config.mailPassword)

	for pair in participantPairs:
		emailResult(pair, server, sentFrom)

	server.close()

def emailResult(pair, server, sentFrom):
	to = pair['Email']
	subject = 'Secret Santa'
	body = pair['Name'] + ' is giving to ' + pair['Receiver']

	msg = MIMEMultipart()
	msg['From'] = sentFrom
	msg['To'] = to
	msg['Subject'] = subject

	msg.attach(MIMEText(body, 'plain'))

	server.sendmail(sentFrom, to, msg.as_string())

@app.route('/clear-results/<family>', methods=['DELETE'])
def clearResults(family):
	password = request.json.get('password', None)

	if password != superSecretPassword:
		return 'You did not say the magic word'

	if not os.path.isfile(family + '.json'):
		return 'No results to clear'

	os.remove(family + '.json')
	return 'Results were cleared'

@app.route('/who-i-am-giving-to/<family>/<giver>')
def displayReceiver(family, giver):
	if not os.path.isfile(family + '.json'):
		return 'That family is not present :('

	with open(family + '.json', 'r') as resultsFile:
		participantPairs = json.load(resultsFile)['results']

	for pair in participantPairs:
		if pair['Name'].lower() == giver.lower():
			return giver + ' is giving to ' + pair['Receiver']

	return 'That person is not in the list :('

@app.route('/generate-results/<family>', methods=['POST'])
def assignNames(family):
	giverNames = extractGiverNames(request.json.get('participants', None))
	giverEmails = extractGiverEmails(request.json.get('participants', None))

	if not giverNames:
		return 'Participants is a required argument'

	if os.path.isfile(family + '.json'):
		return 'There are already generated results!'

	receivers = list(giverNames)
	spouseMapping = request.json.get('spouses', None)

	priorYearFileName = request.json.get('priorYearFileName', None)

	priorYear = None

	if priorYearFileName:
		with open(priorYearFileName, 'r') as priorYearFile:
			priorYear = json.load(priorYearFile)

	if spouseMappingIsValid(giverNames, spouseMapping) and thereAreNoDuplicateParticipants(giverNames) and thereIsAValidResult(giverNames, spouseMapping):
		shuffleReceiversUntilValid(giverNames, receivers, spouseMapping, priorYear)
		with open(family + '.json', 'w') as resultsFile:
			json.dump({'results': createResult(giverNames, giverEmails, receivers)}, resultsFile)

		if request.json['sendEmail']:
			emailResults(family)

		return 'Results generated!'
	else:
		return 'That combination of participants and spouses does not have a possible, valid result'

@app.route('/')
def home():
	return 'Just a boring home page'

if __name__ == '__main__':
	app.run(debug=True)
