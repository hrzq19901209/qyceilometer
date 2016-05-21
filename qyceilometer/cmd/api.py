from qyceilometer.collection import hour as hour_collection
from qyceilometer.collection import day as day_collection
from qyceilometer.collection import week as week_collection
from qyceilometer import service
import datetime
import time
def hour():
	service.prepare_service()
	last = datetime.datetime.now().hour
	while True:
		current = datetime.datetime.utcnow().hour
		if current != last:
			last = current
			hour_collection.hour_collection()
		
		time.sleep(600)

def day():
	service.prepare_service()
	last = datetime.datetime.now().day
	while True:
		current = datetime.datetime.now().day
		if current != last:
			last = current
			day_collection.day_collection()
		
		time.sleep(60*60)

def week():
	service.prepare_service()
	last = time.strftime('%W')
	while True:
		current = time.strftime('%W')
		if current != last:
			last = current
			week_collection.week_collection()
		
		time.sleep(60*60*24)