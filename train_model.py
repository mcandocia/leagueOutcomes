import keras
from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout
import numpy as np
import psycopg2
import sys
import os

NUMBER_CHAMPIONS=132
BATCH_SIZE = 240

class DataFetcher(object):
    def __init__(self, mode='train', averageRanking=2):
        self.conn = psycopg2.connect(
            database='leaguedb',
            user='djmax',
            password='pw',
            host='localhost',
            port=5432
        )
        self.cur = self.conn.cursor()
        #silver-ranked matches in 2016 for ranked solo queue
        role_select = ''
        if mode=='train':
            role_select = "AND learning_role BETWEEN 1 AND 8"
        elif mode=='test':
            role_select = "AND learning_role BETWEEN 9 AND 10"
        elif mode=="valid":
            role_select = "AND learning_role BETWEEN 11 AND 12"
        self.query = """SELECT 
        team1win, champids, tiercodes 
        FROM match_summary WHERE 
        match_type='RANKED_SOLO_5x5' AND
        EXTRACT(year FROM timestamp)=2016 AND
        averageRanking=%d %s
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
        for i, row in enumerate(data):
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
        x = np.concatenate((champ1,champ2,codes1,codes2), axis=1)
        return (x, y)
            

    def fetch_data(self, n=60):
        data = self.cur.fetchmany(n)
        n_results = len(data)
        while n_results < n:
            self.cur.execute(self.query)
            data += self.cur.fetchmany(n - n_results)
            n_results = len(data)
        return self.process_data(data)

def main(*args, **kwargs):
    averageRanking = 1
    os.chdir('/home/max/workspace/league')
    model = Sequential()
    fetcher = DataFetcher(mode='train', averageRanking=averageRanking)
    test_fetcher = DataFetcher(mode='test', averageRanking=averageRanking)
    valid_fetcher = DataFetcher(mode='valid', averageRanking=averageRanking)
    model.add(Dense(output_dim=132, input_dim=280))
    model.add(Dropout(0.5))
    model.add(Activation('relu'))
    model.add(Dense(output_dim=40))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=24))
    model.add(Activation('softmax'))
    model.add(Dense(output_dim=12))
    model.add(Dense( 1, activation="sigmoid"))
    optimizer = keras.optimizers.Nadam(lr=0.004)
    model.compile(loss='binary_crossentropy', 
                  optimizer=optimizer, metrics=['accuracy'])
    for iter in range(9000):
        #print "EPOCH: %d" % iter
        x, y = fetcher.fetch_data(BATCH_SIZE)
        if iter % 100:
            model.train_on_batch(x, y)
        else:
            xt, yt = test_fetcher.fetch_data(1500)
            loss_and_metrics = model.evaluate(xt, yt, batch_size=1200)
            print 'learning rate: %d' % model.optimizer.lr.get_value()
            print iter
            print loss_and_metrics
    xv, yv = valid_fetcher.fetch_data(1500)
    score = model.evaluate(xv, yv, verbose=0)
    print "%s: %.2f%%" % (model.metrics_names[1], score[1]*100)
    model.save_weights("model.h5")
    model_json = model.to_json()
    with open('model.json', 'w') as json_file:
        json_file.write(model_json)
    print 'completed'
        

if __name__=='__main__':
    main(sys.argv[1:])
