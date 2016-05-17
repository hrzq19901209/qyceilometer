python setup.py bdist_wheel
python setup.py install
useradd qyceilometer
dir = /var/log/qyceilometer
mkdir $dir
touch $dir/qyceilometer.log
touch $dir/qyceilometer-hour.log
touch $dir/qyceilometer-day.log
touch $dir/qyceilometer-week.log
chown -R qyceilometer:qyceilometer $dir

. generate-config-file.sh
mkdir /etc/qyceilometer
cp etc/qyceilometer.conf /etc/qyceilometer
cp qyceilometer-hour.conf /etc/init
cp qyceilometer-day.conf /etc/init
cp qyceilometer-week.conf /etc/init
service qyceilometer-hour start
service qyceilometer-day start
service qyceilometer-week start
