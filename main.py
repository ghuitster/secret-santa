from random import shuffle
from flask import Flask, request
import ast
import json
import os.path

app = Flask(__name__)

superSecretPassword = ''

def doesAGiverHaveThemself(givers, receivers):
	for i, giver in enumerate(givers):
		if giver == receivers[i]:
			return False

	return True

def doesAGiverHaveTheirSpouse(givers, receivers, spouseMapping):
	inverseSpouseMapping = {value: key for key, value in spouseMapping.items()}

	for i, receiver in enumerate(receivers):
		if spouseMapping.get(givers[i]) == receiver:
			return True

		if inverseSpouseMapping.get(givers[i]) == receiver:
			return True

	return False

def isResultValid(givers, receivers, spouseMapping):
	return doesAGiverHaveThemself(givers, receivers) and not (spouseMapping and doesAGiverHaveTheirSpouse(givers, receivers, spouseMapping))

def createResult(givers, receivers):
	results = []

	for i, giver in enumerate(givers):
		results.append({giver:receivers[i]})

	return results

def shuffleReceiversUntilValid(givers, receivers, spouseMapping):
	while not isResultValid(givers, receivers, spouseMapping):
		shuffle(receivers)

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

@app.route('/clear-results')
def clearResults():
	password = request.args.get('password')

	if password != superSecretPassword:
		return 'You did not say the magic word'

	if not os.path.isfile('results.json'):
		return 'No results to clear'

	os.remove('results.json')
	return 'Results were cleared'

@app.route('/who-i-am-giving-to/<giver>')
def displayReceiver(giver):
	with open('results.json', 'r') as resultsFile:
		participantPairs = json.load(resultsFile)['results']

	for pair in participantPairs:
		if pair.get(giver, None):
			return giver + ' has ' + pair[giver]

	return 'That person is not in the list :('

@app.route('/generate-results')
def assignNames():
	givers = request.args.get('participants')

	if not givers:
		return 'Participants is a required argument'

	if os.path.isfile('results.json'):
		return 'There are already generated results!'

	givers = givers.split(',')
	receivers = list(givers)
	spouseMapping = ast.literal_eval(request.args.get('spouses', 'None'))

	if(spouseMappingIsValid(givers, spouseMapping) and thereAreNoDuplicateParticipants(givers) and thereIsAValidResult(givers, spouseMapping)):
		shuffleReceiversUntilValid(givers, receivers, spouseMapping)
		with open('results.json', 'w') as resultsFile:
			json.dump({'results':createResult(givers, receivers)}, resultsFile)
		return 'Results generated!'
	else:
		return 'That combination of participants and spouses does not have a possible, valid result'

if __name__ == '__main__':
	app.run(debug=True)