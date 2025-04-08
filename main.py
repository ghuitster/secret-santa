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

def doesAGiverHaveWhoTheyHadInPriorYears(givers, receivers, priorYears):
	for priorYear in priorYears:
		for i, giver in enumerate(givers):
			if getPriorYearReceiver(giver, priorYear) == receivers[i]:
				return True

	return False

def isResultValid(givers, receivers, spouseMapping, priorYears):
	return not doesAGiverHaveThemself(givers, receivers) and not (spouseMapping and doesAGiverHaveTheirSpouse(givers, receivers, spouseMapping)) and not (priorYears and doesAGiverHaveWhoTheyHadInPriorYears(givers, receivers, priorYears))

def createResult(giverNames, giverEmails, receivers):
	results = []

	if request.json['sendEmail']:
		for i, giver in enumerate(giverNames):
			results.append({'Name': giver, 'Email': giverEmails[giver], 'Receiver': receivers[i]})
	else:
		for i, giver in enumerate(giverNames):
			results.append({'Name': giver, 'Receiver': receivers[i]})

	return results

def shuffleReceiversUntilValid(givers, receivers, spouseMapping, priorYears):
	while not isResultValid(givers, receivers, spouseMapping, priorYears):
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

	priorYearsFileNames = request.json.get('priorYearsFileNames', None)

	priorYears = []

	if priorYearsFileNames:
		for priorYearFileName in priorYearsFileNames:
			with open(priorYearFileName, 'r') as priorYearFile:
				priorYears.append(json.load(priorYearFile))

	if spouseMappingIsValid(giverNames, spouseMapping) and thereAreNoDuplicateParticipants(giverNames) and thereIsAValidResult(giverNames, spouseMapping):
		shuffleReceiversUntilValid(giverNames, receivers, spouseMapping, priorYears)
		with open(family + '.json', 'w') as resultsFile:
			json.dump({'results': createResult(giverNames, giverEmails, receivers)}, resultsFile)

		if request.json['sendEmail']:
			emailResults(family)

		return 'Results generated!'
	else:
		return 'That combination of participants and spouses does not have a possible, valid result'

if __name__ == '__main__':
	app.run(debug=True)
