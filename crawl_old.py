#!/home/developer/office.iSetevik/iSetevik/officevenv/bin/python

import requests
from bs4 import BeautifulSoup
import MySQLdb

LOG_URL = "https://office.vilavi.com/Account/Login?ReturnUrl=%2F"
URL = "https://office.vilavi.com/Account/Login?returnurl=%2F"
TREE_URL = "https://office.vilavi.com/Info/GetMlmTree?Generation=All&BcNumber=All&BcSide=All"
payload = {
        'Login': '909555',
        'Password': 'qBEY07!@#'
}

db = MySQLdb.connect(host="localhost",user="isetevik",passwd="isetevik909#",db="isetevik",charset="utf8")
c = db.cursor()
c.execute("""SELECT * FROM web_superadminsettings""")
rows = c.fetchall()
for a in rows:
	payload['Login'] = a[3]
	payload['Password'] = a[4]

print(payload)

def crawl():
    with requests.Session() as c:
        soup = BeautifulSoup(c.get(LOG_URL).content, "html.parser")
        token = soup.find_all('input')
        csrf = ''
        for a in token:
            if a['name'] == '__RequestVerificationToken':
                csrf = a['value']
        payload['__RequestVerificationToken'] = csrf

        thing = c.post(URL, data=payload)
        my_csv = c.get(TREE_URL)
        my_csv.encoding = 'utf-8'
        rows = my_csv.text.split('\n')[1:]
        return list(filter(lambda r:len(r)>0,rows)) 

rows = crawl()

if rows.__len__() > 0:


    db.query('''TRUNCATE TABLE web_previlavifetch''')


    for row in rows:
        cols = row.split(',')
        marker = False
        if cols.__len__() == 14:

            if cols[13] == 'True':
                cols[13] = 1
            else:
                cols[13] = 0

            if cols[1].__len__() == 0:
                cols[1] = 'NULL'
                marker = True
            else:
                cols[1] = int(cols[1])
            print(cols)


    #['28573', None, '1175', '2 CARAT', 'Gold', '0', '909555', 'Зыков К. А. и Савина С. Г.', '77019090555', '26.12.2016', 'Бонусная активность выполнена', 'text-success', 'avatars\\909555.jpeg', False]
            try:

                if marker:
                    sql = "INSERT INTO web_previlavifetch (uid, sid, gpv,r, q, g, ul,un, up, ur, ua,uas, uav, dd) VALUES ('%d',%s,'%d','%s','%s','%d','%d','%s','%s','%s','%s','%s','%s','%d')" % \
                           (int(cols[0]), cols[1], int(cols[2]),cols[3], cols[4], int(cols[5]), int(cols[6]),cols[7], cols[8], cols[9], cols[10], cols[11], cols[12], cols[13] )
                else:
                    sql = "INSERT INTO web_previlavifetch (uid, sid, gpv,r, q, g, ul,un, up, ur, ua,uas, uav, dd) VALUES ('%d','%d','%d','%s','%s','%d','%d','%s','%s','%s','%s','%s','%s','%d')" % \
                           (int(cols[0]), cols[1], int(cols[2]),cols[3], cols[4], int(cols[5]), int(cols[6]),cols[7], cols[8], cols[9], cols[10], cols[11], cols[12], cols[13] )
                c.execute(sql)
                db.commit()

            except:
                print("Couldn't insert record")
            # print(sql)

pre = c.execute('SELECT * FROM web_previlavifetch')
source = c.execute('SELECT * FROM web_vilavifetch')
print(pre)
print(source)
print(pre >= source)

if pre >= source:
    db.query('''TRUNCATE TABLE web_vilavifetch''')
    c.execute('INSERT INTO web_vilavifetch (uid,sid,gpv,r,q,g,ul,un,up,ur,ua,uas,uav,dd) select uid,sid,gpv,r,q,g,ul,un,up,ur,ua,uas,uav,dd from web_previlavifetch')
    db.query('''UPDATE web_superadminsettings set problems = 0, date = NOW() where id = 1''')
    db.query('''update web_tree, web_vilavifetch set web_tree.gpv = web_vilavifetch.gpv, web_tree.ua=web_vilavifetch.ua, web_tree.q=web_vilavifetch.q where web_tree.ul=web_vilavifetch.ul''')
    db.commit()
    print("source upated")
else:
    db.query('''UPDATE web_superadminsettings set problems = 1 where id = 1''')
    db.query('''TRUNCATE TABLE web_vilavifetch''')
    db.commit()
    print("Something is wrong")

db.close()
