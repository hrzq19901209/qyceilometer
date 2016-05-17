from qyceilometer.collection import hour as hour_collection
from qyceilometer.collection import day
from qyceilometer.collection import week
from qyceilometer import service
import datetime
import time
def hour():
	service.prepare_service()
	hour_collection.hour_collection()

	while True:
		current = datetime.datetime.now().hour
		if current != last:
			last = current
			hour_collection.hour_collection()
		
		time.sleep(600)

def day():
	service.prepare_service()
	last = datetime.datetime.now().day
	day.day_collection()
	while True:
		current = datetime.datetime.now().day
		if current != last:
			last = current
			day.day_collection()
		
		time.sleep(60*60)

def week():
	service.prepare_service()
	last = time.strftime('%W')
	week.week_collection()
	while True:
		current = time.strftime('%W')
		if current != last:
			last = current
			week.week_collection()
		
		time.sleep(60*60*24)