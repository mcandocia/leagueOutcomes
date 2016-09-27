import keras
from dbinfo import Database
import numpy as np
from copy import deepcopy

NUMBER_CHAMPIONS = 132
#for testing
DEFAULT_CHAMPIONS = ['Annie','Tryndamere','Twitch','Sona','Akali',
                     'Twisted Fate','Miss Fortune','Gangplank','Leona','Trundle']

bad_champs = ['Annie', 'Ahri', 'Swain', 'Fiddlesticks', 'Zyra', 
              'Ryze', 'Galio', 'Lucian', 'Nami', 'Singed']

popular_champs = ['Vayne','Thresh','Lee Sin','Brand','Rengar',
                  'Ezreal','Kha\'Zix', 'Ekko', 'Braum', 'Diana']

classic_champs = ['Amumu','Annie','Corki','Tryndamere','Singed',
                  'Ashe','Cho\'Gath', 'Karthus', 'Udyr', 'Soraka']

#flips team champs around
def rev5(obj):
    return obj[5:10] + obj[0:5]

RANKING_DICT = {'UNRANKED':[5,0,0,0,0,0,0,0],
                'BRONZE':  [0,5,0,0,0,0,0,0],
                'SILVER':  [0,0,5,0,0,0,0,0],
                'GOLD':    [0,0,0,5,0,0,0,0],
                'PLATINUM':[0,0,0,0,5,0,0,0],
                'DIAMOND': [0,0,0,0,0,5,0,0],
                'MASTER':[0,0,0,0,0,0,5,0],
                'CHALLENGER':[0,0,0,0,0,0,0,5]}
def main():
    pass

def process_data(data, use_names=False):
    """INPUT:
    one-hot-array for all champions on team 1
    one-hot-array for all champions on team 2
    8-array of counts for tier codes for team 1
    8-array of counts for tier codes for team 2
    * if use_names=True, then the database will be used to find matches
      for the names

    OUTPUT:
    binary array of whether team 1 won or lost
    """
    nrows = len(data)
    champ1 = np.zeros((nrows, NUMBER_CHAMPIONS))
    champ2 = np.zeros((nrows, NUMBER_CHAMPIONS))
    codes1 = np.zeros((nrows, 8))
    codes2 = np.zeros((nrows, 8))
    if not isinstance(data, list):
        data = [data]
    if use_names:
        db = Database()
        datacopy = deepcopy(data)
        for i, row in enumerate(datacopy):
            champion_ids = [-1 for _ in range(10)]
            for j, champ_name in enumerate(row['champions']):
                db.cur.execute('''SELECT fixed_id FROM static_champions 
                WHERE name=%s;''',
                               (champ_name,))
                champion_ids[j] = int(db.cur.fetchone()[0])
                data[i]['champions'] = champion_ids
                #print '%s: %d' % (champ_name, champion_ids[j])

    for i, row in enumerate(data):
        for j, champ_id in enumerate(row['champions']):
            if j < 6:
                champ1[i, champ_id-1] = 1
            else:
                champ2[i, champ_id-1] = 1
        for j, value in enumerate(row['rankings']):
            if j<8:
                codes1[i, j] += value
            else:
                codes2[i, j-8] += value
    x = np.concatenate((champ1,champ2,codes1,codes2), axis=1)
    return x

def casual_predict(champions=DEFAULT_CHAMPIONS, ranking='SILVER'):
    """avoids need for extra configuration"""
    if len(ranking) == 2:
            return predict({'champions':champions, 
                            'rankings':RANKING_DICT[ranking[0]] + 
                            RANKING_DICT[ranking[1]]})
    return predict({'champions':champions, 'rankings':RANKING_DICT[ranking] * 2})

def predict(data, model_name = 'model0', root_url = '/home/max/workspace/league/'):
    if isinstance(data, list):
        use_names = isinstance(data[0]['champions'][0], str)
    else:
        use_names = isinstance(data['champions'][0], str)        
    with open(root_url + model_name + '.json', 'r') as f:
        model_json = f.read()
    model = keras.models.model_from_json(model_json)
    model.load_weights(model_name + '.h5')            
    model.compile(loss='binary_crossentropy', optimizer='nadam',
                  metrics=['accuracy'])
    cleaned_data = process_data(data, use_names = use_names)
    predictions = model.predict_proba(cleaned_data, 
                                      batch_size = cleaned_data.shape[0], 
                                      verbose=0)
    print predictions
    return predictions
