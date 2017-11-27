import re

from bs4 import BeautifulSoup
import requests

# .find(id='nameForm')
url = 'https://office.vilavi.com/Account/Register?returnurl=%2F'
import json
# def get_session_id(raw_resp):
#     soup = BeautifulSoup(raw_resp.text, 'lxml')
#     token = soup.find_all('input', {'name':'survey_session_id'})[0]['value']
#     return token
# data = {
# 	"IsResident": False,
# 	"SponsorId": "909555",
# 	"FullName": "Torgayev kassymkhan",
# 	"LastName": "Torgayev",
# 	"FirstName": "kassymkhan",
# 	"MiddleName": "kassymkhan",
# 	"Password": "12asasdasfasdf",
# 	"ConfirmPassword": "12asasdasfasdf",
# 	"Email": "kasim_kazakish@mail.ru",
# 	"PhoneNumber": "+77073716231",
# 	"__RequestVerificationToken": "",
# 	"Agree": True,
#     "Gender": "Male",
# }
class VilaviException(Exception):
    def __init__(self, error_messages):
        self.error_messages = error_messages


def validateVilavi(data):
    with requests.session() as s:
        resp = s.get(url)
        soup = BeautifulSoup(resp.text, 'lxml').find('form')
        for i in soup.find_all('input'):
            # data[i.get('name')] = 'asdasdasd'
            if i.get('name') == "__RequestVerificationToken":
                data["__RequestVerificationToken"] = i.get('value')
        print('\n\n\n\n\n')
        response_post = s.post(url, data=data)
        rsoup = BeautifulSoup(response_post.text, 'lxml')
        print('-------')
        error_list = []
        for j in rsoup.find_all(class_='text-danger'):
            if j.text.strip() != '':
                for k in j.text.split('\n'):
                    error_list.append(k)
        if not error_list:
            try:
                print(rsoup.find_all("span", attrs={"class": "vilavi-text"},
                                      string=re.compile("ID")))
                return rsoup.find_all("span", attrs={"class": "vilavi-text"},
                                      string=re.compile("ID"))[0].text.replace('ID: ', '')
            except:
                print('[Err2]', error_list)
                raise VilaviException(error_list)
        else:
            print('[Err]', error_list)
            raise VilaviException(error_list)
