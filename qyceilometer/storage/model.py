from qyceilometer.storage import base

class Meter(base.Model):
	def __init__(self, name, type, unit, resource_id, project_id, user_id):
		base.Model.__init__(self,
			name=name,
			type=type,
			unit=unit,
			resource_id=resource_id,
			project_id=project_id,
			user_id=user_id)

class Sample(base.Model):
	def __init__(self,
		timestamp,
		counter_name, counter_type, counter_unit, counter_volume,
		user_id, project_id, resource_id):
		base.Model.__init__(self,
                            timestamp=timestamp,
                            counter_name=counter_name,
                            counter_type=counter_type,
                            counter_unit=counter_unit,
                            counter_volume=counter_volume,
                            user_id=user_id,
                            project_id=project_id,
                            resource_id=resource_id)
