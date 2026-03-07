
import ast

f = open("data/data.txt", "r")

content = ast.literal_eval(f.read())

nb_activities = len(content[0])
print(nb_activities)
for i in range(nb_activities):
    print(len(content[0][i]))

#print(data)
#print(data.keys())
#print(data['activityId'])
"""
for i in data.keys():
    print(f"key: {i} value: {data[i]}")
"""

hr_keys = ['averageHR', 'maxHR', 'hrTimeInZone_1', 'hrTimeInZone_2', 'hrTimeInZone_3', 'hrTimeInZone_4', 'hrTimeInZone_5']

breath_keys = ['minRespirationRate', 'maxRespirationRate', 'avgRespirationRate']

athlete_keys = ['vO2MaxValue']

training_effect_keys = ['intensityFactor', 'trainingStressScore', 'aerobicTrainingEffect', 'anaerobicTrainingEffect', 'trainingEffectLabel',
                         'activityTrainingLoad', 'aerobicTrainingEffectMessage', 'anaerobicTrainingEffectMessage']

activity_keys = [['activityType', 'typeKey'], 'duration', 'elapsedDuration', 'movingDuration', 'beginTimestamp', 'startTimeLocal', 'startTimeGMT','endTimeGMT']

power_keys = ['avgPower', 'maxPower', 'normPower', 'max20MinPower', 'maxAvgPower_1', 'maxAvgPower_2', 'maxAvgPower_5', 
              'maxAvgPower_10', 'maxAvgPower_20', 'maxAvgPower_30', 'maxAvgPower_60', 'maxAvgPower_120', 'maxAvgPower_300', 
              'maxAvgPower_600', 'maxAvgPower_1200', 'maxAvgPower_1800', 'maxAvgPower_3600', 'maxAvgPower_7200', # maxAvgPower_valeur, la valeur dépend de la longueur de la sortie
              'powerTimeInZone_1', 'powerTimeInZone_2', 'powerTimeInZone_3', 'powerTimeInZone_4', 'powerTimeInZone_5','powerTimeInZone_6', 'powerTimeInZone_7', 
              'avgLeftBalance']   

cadence_keys = ['averageBikingCadenceInRevPerMinute', 'maxBikingCadenceInRevPerMinute', '']

speed_keys = ['maxSpeed', 'maxVerticalSpeed']   # vitesse en m/s

# 'strokes' ?

energy_keys = ['waterEstimated', 'bmrCalories', 'differenceBodyBattery']

route_keys = ['distance', 'startLatitude', 'startLongitude', 'minElevation', 'maxElevation', 'avgElevation', 'locationName', 'endLatitude', 'endLongitude', '']

temp_keys = ['minTempertature', 'maxTemperature']

f.close()