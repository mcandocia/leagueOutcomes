import keras
from dbinfo import Database
import numpy as np
from copy import deepcopy
import time
import sys

NUMBER_CHAMPIONS = 133
MAX_PATCH_VALUE = 43
#for testing
DEFAULT_CHAMPIONS = ['Annie','Tryndamere','Twitch','Sona','Akali',
                     'Twisted Fate','Miss Fortune','Gangplank','Leona','Trundle']

bad_champs = ['Annie', 'Ahri', 'Swain', 'Fiddlesticks', 'Zyra', 
              'Ryze', 'Galio', 'Lucian', 'Nami', 'Singed']

popular_champs = ['Vayne','Thresh','Lee Sin','Brand','Rengar',
                  'Ezreal','Kha\'Zix', 'Ekko', 'Braum', 'Diana']

classic_champs = ['Amumu','Annie','Corki','Tryndamere','Singed',
                  'Ashe','Cho\'Gath', 'Karthus', 'Udyr', 'Soraka']

lower_rankings = ['UNRANKED','BRONZE','SILVER','GOLD']
upper_rankings = ['PLATINUM','DIAMOND','MASTER','CHALLENGER']

#flips team champs around
def rev5(obj):
    return obj[5:10] + obj[0:5]

RANKING_DICT = {'UNRANKED':[4,1,0,0,0,0,0,0],
                'BRONZE':  [1,3,1,0,0,0,0,0],
                'SILVER':  [0,1,3,1,0,0,0,0],
                'GOLD':    [0,0,1,3,1,0,0,0],
                'PLATINUM':[0,0,0,1,3,1,0,0],
                'DIAMOND': [0,0,0,0,1,3,1,0],
                'MASTER':[0,0,0,0,0,1,3,1],
                'CHALLENGER':[0,0,0,0,0,0,1,4]}
def main(model_number = 0):
    model_number = int(model_number)
    print 'testing champs'
    for rank in lower_rankings:
        time.sleep(1.5)
        print 'RANK: %s' % rank
        print DEFAULT_CHAMPIONS
        casual_predict(DEFAULT_CHAMPIONS, rank, model_number)
        print rev5(DEFAULT_CHAMPIONS)
        casual_predict(rev5(DEFAULT_CHAMPIONS), rank, model_number)
        print bad_champs
        casual_predict(bad_champs, rank, model_number)
        print rev5(bad_champs)
        casual_predict(rev5(bad_champs), rank, model_number)
        print classic_champs
        casual_predict(classic_champs, rank, model_number)
        print rev5(classic_champs)
        casual_predict(rev5(classic_champs), rank, model_number)
        print popular_champs
        casual_predict(popular_champs, rank, model_number)
        print rev5(popular_champs)
        casual_predict(rev5(popular_champs), rank, model_number)
    print 'done predicting via main()'

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
    patch_matrix = np.zeroes((nrows, MAX_PATCH_VALUE + 1))
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
        #create patch data
        if 'patch_id' in row:
            patch_matrix[i, row['patch_id']] = 1
        else:
            patch_matrix[MAX_PATCH_VALUE] = 1
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
    x = np.concatenate((champ1,champ2,codes1,codes2, patch_matrix), axis=1)
    return x

def casual_predict(champions=DEFAULT_CHAMPIONS, ranking='SILVER', model_number=0):
    """avoids need for extra configuration"""
    if len(ranking) == 2:
            return predict({'champions':champions, 
                            'rankings':RANKING_DICT[ranking[0]] + 
                            RANKING_DICT[ranking[1]]})
    return predict({'champions':champions, 'rankings':RANKING_DICT[ranking] * 2},
                   model_name = 'model%d' % model_number)

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

if __name__=='__main__':
    main(sys.argv[1])
