#!/home/developer/office.iSetevik/iSetevik/officevenv/bin/python

import requests,requests.utils, pickle
from bs4 import BeautifulSoup
import MySQLdb

mysqllogin='isetevik'
mysqlpwd='isetevik909#'
mysqldb='isetevik'
LOG_URL = "https://office.vilavi.com/Account/Login?ReturnUrl=%2F"
URL = "https://office.vilavi.com/Account/Login?returnurl=%2F"
TREE_URL = "https://office.vilavi.com/Info/GetMlmTree?Generation=All&BcNumber=All&BcSide=All"
payload = {
        'Login': '909555',
        'Password': 'qBEY07!@#'
}
path_to_cookies_file='/home/rassul/session.txt'

def log(message,cursor=None):
    if (cursor is not None): 
       cursor.execute("insert into crawler_log(message) values ('%s')" % message.replace("'","#"))
    print(message)

def start():
    db = MySQLdb.connect(host="localhost",user=mysqllogin,passwd=mysqlpwd,db=mysqldb,charset="utf8")
    c = db.cursor()
    c.execute('SELECT * FROM crawler_status where ID=1')
    row = c.fetchone()
    if row[1]>10:
        c.execute('UPDATE crawler_status set status=0,starttime=null,endtime=null')
        c.execute("insert into crawler_log(message) values('tried 10 times, reseting!')")
        db.commit()
        db.close()
        return False
    if row[1]>0:
        c.execute('update crawler_status set status=status+1')
        c.execute("insert into crawler_log(message) values('next attempt')")
        db.commit()
        db.close()
        return False
    else:
        c.execute('UPDATE crawler_status set status=1,starttime=NOW(),endtime=NULL,lmessage=NULL where ID = 1')
        db.commit()
    db.close()
    return True;
def end(status,lastmessage):
    db = MySQLdb.connect(host="localhost",user=mysqllogin,passwd=mysqlpwd,db=mysqldb,charset="utf8")
    c = db.cursor()
    c.execute("UPDATE crawler_status set status=%d,endtime=NOW(),lmessage='%s' where ID = 1" % (status,lastmessage))
    db.commit()
    db.close()
def crawl():
    db = MySQLdb.connect(host="localhost",user=mysqllogin,passwd=mysqlpwd,db=mysqldb,charset="utf8")
    c = db.cursor()
    c.execute('SELECT * FROM web_superadminsettings')
    rows = c.fetchall()
    for a in rows:
        payload['Login'] = a[3]
        payload['Password'] = a[4]
    db.close()
    with requests.Session() as c:
        set_cookies(c)
        my_csv = get_csv(c)
        if "uId,sId,gpv,r,q,g,uL,uN,uP,uR,uA,uAs,uAv,dd" not in my_csv.text: 
            refresh_cookies(c)
            my_csv = get_csv(c)
        rows = my_csv.text.split('\n')[1:]
        return list(filter(lambda r:len(r)>0,rows))    

def refresh_cookies(session):
    with requests.Session() as c:
        soup = BeautifulSoup(c.get(LOG_URL).content, "html.parser")
        token = [x for x in soup.find_all('input') if x['name']=='__RequestVerificationToken']
        payload['__RequestVerificationToken'] = token[0]['value'] 
        thing = c.post(URL, data=payload)
        with open(path_to_cookies_file, 'wb') as f:
           pickle.dump(requests.utils.dict_from_cookiejar(c.cookies), f)
        session.cookies = c.cookies

def set_cookies(session):
    with open(path_to_cookies_file,'rb') as f:
           cookies = requests.utils.cookiejar_from_dict(pickle.load(f))
           session.cookies = cookies

def get_csv(session):
    my_csv = session.get(TREE_URL)
    my_csv.encoding = 'utf-8'
    return my_csv

def migrate():
    log('migrate-begin')
    FILL_TREE = "http://office.isetevik.com/fill_all_tree/"
    db = MySQLdb.connect(host="localhost",user=mysqllogin,passwd=mysqlpwd,db=mysqldb,charset="utf8")
    c = db.cursor()
    c.execute('SELECT count(*) FROM web_vilavifetch')
    source_count = c.fetchone()
    c.execute('SELECT count(*) FROM web_previlavifetch')
    stage_count = c.fetchone()
    if(stage_count[0]>0):
        c.execute('delete from web_vilavifetch')
        c.execute('INSERT INTO web_vilavifetch (uid,sid,gpv,r,q,g,ul,un,up,ur,ua,uas,uav,dd) select uid,sid,gpv,r,q,g,ul,un,up,ur,ua,uas,uav,dd from web_previlavifetch')
        c.execute('UPDATE web_superadminsettings set problems = 0, date = NOW() where id = 1')
        c.execute('update web_tree, web_vilavifetch set web_tree.uid=web_vilavifetch.uid,web_tree.sid=web_vilavifetch.sid, web_tree.gpv = web_vilavifetch.gpv, web_tree.ua=web_vilavifetch.ua, web_tree.q=web_vilavifetch.q where web_tree.ul=web_vilavifetch.ul')
        c.execute('update web_tree set active = 0 where ul in (select ul from (select ul from web_tree w where not exists (select uid from web_tree wt where wt.sid=w.uid) and datediff(now(),str_to_date(ur,\'%d.%m.%Y\')) > 60 and ul not in (select ul from web_vilavifetch)) ssq)');
        c.execute('delete from web_tree where active = 0 and ul in (select ul from (select ul from web_tree w where not exists (select uid from web_tree wt where wt.sid=w.uid) and active = 0 and datediff(now(),str_to_date(ur,\'%d.%m.%Y\')) > 120 and ul not in (select ul from web_vilavifetch)) ssq)');
        db.commit()
        with requests.Session() as s:
            s.get(FILL_TREE)
    else:
        log('stage empty',c)
        c.execute('UPDATE web_superadminsettings set date = NOW() where id = 1')
        db.commit()
    db.close()
    log('migrate-end')
def populate():
    log('crawl-begin')
    rows = crawl()
    log('crawl-end')
    log('records crawled:%d' % rows.__len__())
    db = MySQLdb.connect(host="localhost",user=mysqllogin,passwd=mysqlpwd,db=mysqldb,charset="utf8")
    c = db.cursor()
    if rows.__len__() > 0:
        c.execute('TRUNCATE TABLE web_previlavifetch')
        print('truncated web_previlavifetch')
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
                try:
                    if marker:
                        sql = "INSERT INTO web_previlavifetch (uid, sid, gpv,r, q, g, ul,un, up, ur, ua,uas, uav, dd) VALUES ('%d',%s,'%d','%s','%s','%d','%d','%s','%s','%s','%s','%s','%s','%d')" % \
                               (int(cols[0]), cols[1], int(cols[2]),cols[3], cols[4], int(cols[5]), int(cols[6]),cols[7], cols[8], cols[9], cols[10], cols[11], cols[12], cols[13] )
                    else:
                        sql = "INSERT INTO web_previlavifetch (uid, sid, gpv,r, q, g, ul,un, up, ur, ua,uas, uav, dd) VALUES ('%d','%d','%d','%s','%s','%d','%d','%s','%s','%s','%s','%s','%s','%d')" % \
                               (int(cols[0]), cols[1], int(cols[2]),cols[3], cols[4], int(cols[5]), int(cols[6]),cols[7], cols[8], cols[9], cols[10], cols[11], cols[12], cols[13] )
                    c.execute(sql)
                except:
                    #c.execute('UPDATE web_superadminsettings set problems = 1 where id = 1')
                    #db.commit()
                    #db.close()
                    log('could not insert record: %s' % sql,c)
                    #return False
            else:
                c.execute('UPDATE web_superadminsettings set problems = 1 where id = 1')
                log('Number of columns changed!',c)
                db.commit()
                db.close()
                return False 
        db.commit()
        db.close()
        return True
    else:
        c.execute('UPDATE web_superadminsettings set problems = 1 where id = 1')
        log('Nothing came from  VILAVI',c)
        db.commit()
        db.close()
        return False
if start():
    if populate():
        migrate()
        end(0,'ok')
    else:
        log('not populated')
        end(1,'not populated')
else:
    log('Can not start')

