from qyceilometer.collection import hour
from qyceilometer import service
import datetime

def main():
	service.prepare_service(log_files='/var/log/ceilometer/qyceilometer.log', 
		config_files=['/etc/ceilometer/qyceilometer.conf'])
	last = datetime.datetime.now().hour
	hour.hour_collection()
	while True:
		current = datetime.datetime.now().hour
		if current != last:
			last = current
			hour.hour_collection()
		
		time.sleep(600)
