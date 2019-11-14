from random import shuffle
from flask import Flask, request
import ast
import json
import os.path
import random

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

def lower_dict_keys(d):
	new_dict = dict((k.lower(), v) for k, v in d.items())
	return new_dict

@app.route('/clear-results/<family>', methods=['DELETE'])
def clearResults(family):
	password = request.args.get('password')

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
		pair = lower_dict_keys(pair)

		if pair.get(giver.lower(), None):
			return giver + ' has ' + pair[giver.lower()]

	return 'That person is not in the list :('

@app.route('/generate-results/<family>', methods=['POST'])
def assignNames(family):
	givers = request.json.get('participants', None)

	if not givers:
		return 'Participants is a required argument'

	if os.path.isfile(family + '.json'):
		return 'There are already generated results!'

	receivers = list(givers)
	spouseMapping = request.json.get('spouses', None)

	if(spouseMappingIsValid(givers, spouseMapping) and thereAreNoDuplicateParticipants(givers) and thereIsAValidResult(givers, spouseMapping)):
		shuffleReceiversUntilValid(givers, receivers, spouseMapping)
		with open(family + '.json', 'w') as resultsFile:
			json.dump({'results':createResult(givers, receivers)}, resultsFile)
		return 'Results generated!'
	else:
		return 'That combination of participants and spouses does not have a possible, valid result'

@app.route('/')
def home():
	return 'Just a boring home page'

if __name__ == '__main__':
	app.run(debug=True)
