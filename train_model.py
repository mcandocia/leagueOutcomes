import keras
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
from keras.regularizers import l2
import numpy as np
import psycopg2
import sys
import os
from dbinfo import Database

NUMBER_CHAMPIONS = 133
BATCH_SIZE = 200
#helps enforce semblance of symmetry in training
TEAM_FLIP_CHANCE = 0.375
#currently unused
TRAGIC_FLIP_CHANCE = 0.02
#this makes sure the code is compatible with previous versions
MAX_PATCH_VALUE = 43
#              2 for each team     patch version + offset league rankings
INPUT_DIM = NUMBER_CHAMPIONS * 2 + MAX_PATCH_VALUE + 1 +   8*2

class DataFetcher(object):
    def __init__(self, mode='train', averageRanking=2):
        self.db = Database()
        self.conn = self.db.conn
        self.cur = self.db.cur
        #silver-ranked matches in 2016 for ranked solo queue
        role_select = ''
        if mode=='train':
            role_select = "AND learning_role BETWEEN 1 AND 8"
        elif mode=='test':
            role_select = "AND learning_role BETWEEN 9 AND 10"
        elif mode=="valid":
            role_select = "AND learning_role BETWEEN 11 AND 12"
        self.query = """SELECT 
        team1win, champids, tiercodes, match_version_code
        FROM match_summary WHERE 
        match_type='RANKED_SOLO_5x5' AND
        match_version_code IS NOT NULL AND--%d
        averageRanking<7 %s--temporary hardcode to allow for more general results
        ORDER BY random();""" % (averageRanking, role_select)
        self.cur.execute(self.query)

    def process_data(self, data):
        """INPUT:
        one-hot-array for all champions on team 1
        one-hot-array for all champions on team 2
        8-array of counts for tier codes for team 1
        8-array of counts for tier codes for team 2
        
        OUTPUT:
        binary array of whether team 1 won or lost
        """
        y = np.asarray([x[0]*1 for x in data])        
        nrows = len(data)
        champ1 = np.zeros((nrows, NUMBER_CHAMPIONS))
        champ2 = np.zeros((nrows, NUMBER_CHAMPIONS))
        codes1 = np.zeros((nrows, 8))
        codes2 = np.zeros((nrows, 8))
        patch_matrix = np.zeros((nrows, MAX_PATCH_VALUE + 1))
        for i, row in enumerate(data):
            patch_matrix[i, row[3]] = 1
            for j, champ_id in enumerate(row[1]):
                if j < 6:
                    champ1[i, champ_id-1] = 1
                else:
                    champ2[i, champ_id-1] = 1
            for j, tier in enumerate(row[2]):
                if j<6:
                    codes1[i, tier] +=1
                else:
                    codes2[i, tier] +=1
        if np.random.random() < TEAM_FLIP_CHANCE:
            x = np.concatenate((champ2,champ1,codes2,codes1, patch_matrix), axis=1)
            y = np.asarray([1 - v for v in y])
        else:
            x = np.concatenate((champ1,champ2,codes1,codes2, patch_matrix), axis=1)
        return (x, y)
            

    def fetch_data(self, n=60):
        data = self.cur.fetchmany(n)
        n_results = len(data)
        while n_results < n:
            self.cur.execute(self.query)
            data += self.cur.fetchmany(n - n_results)
            n_results = len(data)
        return self.process_data(data)

def model1(l2c = 0.0000002):
    """deep model"""
    model = Sequential()
    model.add(Dense(output_dim=132, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=40, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=24, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=12, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model2(l2c = 0.0000002):
    """linear model"""
    model = Sequential()
    model.add(Dense(output_dim=132, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model3(l2c = 0.0000002):
    """1-hidden layer model"""
    model = Sequential()
    model.add(Dense(output_dim=132, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dense(16, activation='softmax', W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model4(l2c = 0.0000002):
    """deeper model"""
    model = Sequential()
    model.add(Dense(output_dim=132, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=40, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=24, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=12, W_regularizer = l2(l2c)))
    model.add(Dropout(0.1))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=5, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam(lr=0.003)
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model5(l2c = 0.0000002):
    """narrow deep model"""
    model = Sequential()
    model.add(Dense(output_dim=32, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=24, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=12, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=10, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model6(l2c = 0.0000002):
    """very narrow & deep model"""
    model = Sequential()
    model.add(Dense(output_dim=30, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=20, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=10, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=8, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=6, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=6, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=4, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model7(l2c = 0.0000002):
    """very deep model"""
    model = Sequential()
    model.add(Dense(output_dim=120, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=72, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=60, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=40, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=32, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=24, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model8(l2c = 0.0000002):
    """deep and wide model"""
    model = Sequential()
    model.add(Dense(output_dim=256, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=256, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=256, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=256, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model

def model9(l2c = 0.0000002):
    """narrow deep model (but slightly wider)"""
    model = Sequential()
    model.add(Dense(output_dim=40, input_dim=INPUT_DIM, W_regularizer = l2(l2c)))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=32, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=16, W_regularizer = l2(l2c)))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=12, W_regularizer = l2(l2c)))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam()
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    return model
    
    
def main(*args, **kwargs):
    averageRanking = 1
    fetcher = DataFetcher(mode='train', averageRanking=averageRanking)
    test_fetcher = DataFetcher(mode='test', averageRanking=averageRanking)
    valid_fetcher = DataFetcher(mode='valid', averageRanking=averageRanking)
    os.chdir('/home/max/workspace/league')
    #models = [model1(), model2(), model3(), model4(), model5(), model6(),
    #          model7(), model8()]
    l2c_values = [0, 5e-9,5e-8, 5e-7, 5e-6, 1e-5, 1e-4, 1e-3]
    models = []
    for l2c in l2c_values:
        models += [model1(l2c), model5(l2c), model9(l2c)]
    #models = [models[0]]#temporary testing
    best_accuracy = [0. for _ in models]
    for iter in range(9000):
        #print "EPOCH: %d" % iter
        x, y = fetcher.fetch_data(BATCH_SIZE)
        if iter % 1000:
            for model in models:
                model.train_on_batch(x, y)
        else:
            xt, yt = test_fetcher.fetch_data(5000)
            for k, model in enumerate(models):
                loss_and_metrics = model.evaluate(xt, yt, batch_size=5000)
                if loss_and_metrics[1] > best_accuracy[k]:
                    model.save_weights("model%d.h5" % k)
                    best_accuracy[k] = loss_and_metrics[1]
                    model_json = model.to_json()
                    with open('model%d.json' % k, 'w') as json_file:
                        json_file.write(model_json)
                        print hilite(loss_and_metrics,0)
                else:
                    with open('model%d.json' % k, 'r') as f:
                        #model_json = f.read()
                        #model.load_weights('model%d.h5' % k)            
                        pass
                    print hilite(loss_and_metrics,1)
            print iter
    xv, yv = valid_fetcher.fetch_data(5000)
    for k, model in enumerate(models):
        #with open('model%d.json' % k, 'r') as f:
        #model_json = f.read()
        #model = keras.models.model_from_json(model_json)
        #model.load_weights('model%d.h5' % k)            
        #model.compile(loss='binary_crossentropy', optimizer='nadam',
        #              metrics=['accuracy'])
        score = model.evaluate(xv, yv, verbose=0)
        print k + 1
        print "%s: %.2f%%" % (model.metrics_names[1], score[1]*100)
    print 'completed'
        

def hilite(string, status, bold = True):
    attr = []
    if status==0:
        # green
        attr.append('42')
    elif status==1:
        # red
        attr.append('41')
    elif status==2:
        #yellow
        attr.append('43')
    if bold:
        attr.append('1')
    return '\x1b[%sm%s\x1b[0m' % (';'.join(attr), string)

def rev5(obj):
    return obj[5:10] + obj[0:5]

#should randomly switch a 1 with a 0
#second part (not in this func) should have 50% of flipping victory
def tragic_flip(data):
    pass

if __name__=='__main__':
    main(sys.argv[1:])
