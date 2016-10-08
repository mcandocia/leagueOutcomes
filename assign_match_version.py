from dbinfo import Database
from datetime import datetime as dt

#lower bounds for dates of patches

patchinfo = [
    (dt(2016,10,5), '6.20'),
    (dt(2016,9,21), '6.19'),
    (dt(2016,9,8), '6.18'),
    (dt(2016,8,24), '6.17'),
    (dt(2016,8,10), '6.16'),
    (dt(2016,7,26), '6.15'),
    (dt(2016,7,13), '6.14'),
    (dt(2016,6,29), '6.13'),
    (dt(2016,6,15), '6.12'),
    (dt(2016,6,1), '6.11'),
    (dt(2016,5,18), '6.10'),
    (dt(2016,5,4), '6.9'),
    (dt(2016,4,20), '6.8'),
    (dt(2016,4,6), '6.7'),
    (dt(2016,3,23), '6.6'),
    (dt(2016,3,9), '6.5'),
    (dt(2016,2,24), '6.4'),
    (dt(2016,2,10), '6.3'),
    (dt(2016,1,28), '6.2'),
    (dt(2016,1,14), '6.1'),
    (dt(2015,12,9), '5.24'),
    (dt(2015,11,24), '5.23'),
    (dt(2015,11,11), '5.22'),
    (dt(2015,10,29), '5.21'),
    (dt(2015,10,14), '5.20'),
    (dt(2015,9,30), '5.19'),
    (dt(2015,9,16), '5.18'),
    (dt(2015,9,2), '5.17'),
    (dt(2015,8,20), '5.16'),
    (dt(2015,8,5), '5.15'),
    (dt(2015,7,22), '5.14'),
    (dt(2015,7,8), '5.13'),
    (dt(2015,6,24), '5.12'),
    (dt(2015,6,10), '5.11'),
    (dt(2015,5,28), '5.10'),
    (dt(2015,5,14), '5.9'),
    (dt(2015,4,28), '5.8'),
    (dt(2015,4,8), '5.7'),
    (dt(2015,3,25), '5.6'),
    (dt(2015,3,12), '5.5'),
    (dt(2015,2,25), '5.4'),
    (dt(2015,2,11), '5.3'),
    (dt(2015,1,28), '5.2'),
    (dt(2015,1,15), '5.1'),
    (dt(2014,12,10), '4.21')
]

def main():
    db = Database()
    db.cur.execute("""DROP TABLE IF EXISTS match_versions;""")
    db.cur.execute("""CREATE TABLE match_versions(
    version TEXT, 
    start_date TIMESTAMP, 
    class_id INTEGER);""")
    db.conn.commit()
    for i, entry in enumerate(patchinfo[::-1]):
        db.cur.execute("""INSERT INTO match_versions VALUES(%s, %s, %s)""",
                       (entry[1], entry[0], i))
        db.conn.commit()
    print 'inserted version information'

if __name__=='__main__':
    main()
