from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.shortcuts import HttpResponseRedirect
from .forms import *
from .models import *
import json
from django.http import JsonResponse
import string, random
from .tasks import send_emails, send_vilavi_id
from django.http import HttpResponse, HttpResponseNotFound
import requests
from bs4 import BeautifulSoup
import codecs
import datetime, pytz
from django.template import RequestContext

def getProfileName(request):
    person = Profile.objects.get(user = request.user.username)
    text = person.name
    return text

@login_required
def personal_area(request):
    username = getProfileName(request)
    return render(request, 'web/personalArea.html', {'username': username})

def logout_view(request):
    logout(request)
    return redirect('user_authentication')

class PasswordChangeView(View):
    form_class = PasswordChangeForm
    template_name = 'web/change_password.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})
    def post(self, request):
        form = self.form_class(user = request.user, data = request.POST)


        if form.is_valid():
            print(form)
            print(request.user)
            user = request.user
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            update_session_auth_hash(request, request.user)
            return redirect('check_tree_vertical')

        return render(request, self.template_name, {'form': form})

class UserFormView(View):
    form_class = UserCreationForm
    template_name = 'web/registration.html'

    def syncProfile(self, username):
        profile = Profile.objects.get(user=username)
        vilProf = VilaviFetch.objects.get(ul=int(username))
        profile.name = vilProf.un
        profile.phone = "+" + vilProf.up
        profile.save()

    def get(self, request):
        sponsor_id = request.GET.get('sponsor_id', None)
        if not sponsor_id:
            print('[NO CURATOR]')
            return redirect('http://video.isetevik.com/start')
            # return render(request, 'web/start.html')
        print('[SPO]', sponsor_id)

        if request.user.is_authenticated:
            return redirect('/myroom/check_tree/vertical')
        form = self.form_class(initial={'sponsor_id': sponsor_id})
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)

        if form.is_valid():
            try:
                user = form.save(commit=False)
            except(VilaviException) as e:
                print('[Val faiked]', e.error_messages)
                return render(request, self.template_name, {'form': form, 'error_list': e.error_messages})
            # cleaned (normalized) data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            Profile.objects.create(user=user.username,
                                   name="{} {} {}".format(
                                        form.cleaned_data['name'],
                                        form.cleaned_data['surname'],
                                        form.cleaned_data['fathers_name']).strip(),
                                   phone=form.cleaned_data['phone'],
                                   email=form.cleaned_data['email'])

            # self.syncProfile(username = username)

            # return User object s if credentials are correct
            user = authenticate(username=username, password=password)

            if user is not None and user.is_active:
                send_vilavi_id(user.email, password, user, username)
                login(request, user)
                return redirect('/myroom/edit_profile')
        return render(request, self.template_name, {'form': form})


class ExistingUserFormView(UserFormView):
    form_class = ExistingUserCreationForm
    template_name = 'web/registration.html'

    def get(self, request):
        # sponsor_id = request.GET.get('sponsor_id', None)
        # if not sponsor_id:
        #     print('[NO CURATOR]')
        #     return redirect('http://vtest.isetevik.com/start')
        #     # return render(request, 'web/start.html')
        # print('[SPO]', sponsor_id)

        if request.user.is_authenticated:
            return redirect('/myroom/check_tree/vertical')
        # initial = {'sponsor_id': sponsor_id}
        form = self.form_class()
        return render(request, self.template_name, {'form': form, 'existing': True})

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():

            user = form.save(commit=False)

            # cleaned (normalized) data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()

            Profile.objects.create(user=user.username)

            self.syncProfile(username=username)

            # return User object s if credidentials are correct
            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('fill_tree_table')
        return render(request, self.template_name, {'form': form})

class UserSignFormView(View):
    form_class = UserAuthenticationForm
    template_name = 'web/signIn.html'

    def allowed(self, profile_id):
        profile = Profile.objects.get(user = profile_id)
        if profile.active:
            return True
        return False

    def get(self, request):
        if request.user.is_authenticated:
            if self.allowed(request.user.username):
                return redirect('fill_tree_table')
            else:
                return redirect(reverse_lazy(logout))

        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})


    def post(self, request):
        form = self.form_class(request.POST)
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        print("OLOLOL")
        print(form.is_valid())

        if form.is_valid():
            if user is not None:
                if user.is_active:
                    login(request, user)
                    print(user)
                    return redirect('fill_tree_table')
        return render(request, self.template_name, {'form': form})




@method_decorator(login_required, name='get')
class EditProfileView(View):
    form_class = EditProfileForm
    template_name = 'web/personalAreaEditProfile.html'
    isAdmin = False

    def get(self, request, pk = None):

        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        if pk is None:
            isChild = False
            my_profile = Profile.objects.get(user=request.user)
        elif pk == request.user.username:
            return redirect("edit_profile")
        else:
            isChild = True
            my_profile = get_object_or_404(Profile, user=pk)

        print("profile is " + str(my_profile))
        profile_form = self.form_class(instance=my_profile)



        return render(request, self.template_name, {
            'form': profile_form,
            'username': username,
            'id': my_profile.user,
            'child': isChild,
            'isAdmin': self.isAdmin,
        })

    def post(self, request, pk):


        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        if pk is None:
            isChild = False
            my_profile = Profile.objects.get(user=request.user)
        elif pk == request.user.username:
            return redirect("edit_profile")
        else:
            isChild = True
            my_profile = get_object_or_404(Profile, user=pk)

        profile_form = self.form_class(request.POST, instance=my_profile)



        if profile_form.is_valid() :

            obj = profile_form.save(commit=False)
            if isChild:
                obj.user = pk
            else :
                obj.user = request.user.username


            city = City.objects.get(name=profile_form.__getitem__("mycity").value())
            country = Country.objects.get(name=city.country)
            my_profile.__setattr__("country", Country.objects.get(name=country))
            my_profile.__setattr__("city", City.objects.get(name=city))

            obj.save()

            if pk is None:
                return redirect('edit_profile')
            else :
                return redirect('/myroom/edit_profile/' + str(pk))



        else:
            return render(request, self.template_name, {
                'profile_form': profile_form,
                'username' :username,
                'id': my_profile.user,
                'child': isChild,
                'isAdmin': self.isAdmin,
            })


@csrf_exempt
def filterCities(request):
    if request.method == 'POST':
        print(request.POST)
        val = request.POST.get('country')
        if val is None:
            id = request.POST.get('id')
            # check if id is not fucked up being 1 =:> 000001
            if len(id) < 6:
                id = "0"*(6-len(id)) + str(id)
            print(id)
            ##finish check
            prof = Profile.objects.get(user=id)
            return JsonResponse({'city': prof.city.name, 'country': prof.country.name})

        if (val is "") or ("---" in val):
            cities = City.objects.all().order_by("country")
            country = Country.objects.all()
        else :
            country = Country.objects.get(name=val)
            cities = City.objects.all().filter(country=country.pk)
        if cities.exists():
            result = {}
            for countr in country:
                result[countr.name] = []
            for city in cities:
                result[city.country.name].append(city.name)
            return JsonResponse(result)
        else:
            return JsonResponse({'error': 'sorry, fuckoff'})

    else:
        return JsonResponse({'error': 'sorry, fuckoff'})

@csrf_exempt
def countryList(request):
    try:
        countries = Country.objects.all().order_by('name')
        result = {}
        result['response'] = []
        for country in countries:
            result['response'].append(country.name)

        return JsonResponse(result)

    except:
        return JsonResponse({'error': 'sorry, fuckoff'})

@csrf_exempt
def cityListByCountry(request):
    if request.method == 'POST':
        country = request.POST.get('country')
        couObj = get_object_or_404(Country, name=country)
        cities = City.objects.filter(country = couObj).order_by('name')
        result = {'response': []}
        for city in cities:
            result['response'].append(city.name)

        return JsonResponse(result)

    else:
        return JsonResponse({'error': 'sorry, fuckoff'})


@csrf_exempt
def vilaviActivity(request):
    if request.method == 'POST':
        ul = request.POST.get('ul')
        id = request.POST.get('id')
        print("UL HAVE ARRIVED")
        print(id)
        print(ul)


        # profile = get_object_or_404(Profile, user=id)
        # treeObj = Tree.objects.filter(profile = profile).filter(ul = ul)[0]
        # listWithValues = []
        # treeObj.__setattr__("active", not treeObj.active)
        # treeObj.save()
        # a = {'name': treeObj.ul}
        # if treeObj.active:
        #     if treeObj.ua == "Активность не выполнена":
        #         a['color'] = "#ff4d4d" #red
        #     else:
        #         a['color'] = "#1a8cff" #blue
        #
        # else:
        #     a['color'] = "#37474f" #grey
        #
        # listWithValues.append(a)
        # return JsonResponse( {'not_active_node': [ul]} )

        if id == ul:
            return JsonResponse({ 'node_list': [] })
        profile = get_object_or_404(Profile, user = id)
        # grandNode = dataForTreeFromTable(forD3=False, profileObject=profile, onlyActive=False)
        # targetNode = findNode(grandNode, request.POST.get('ul'))
        # children_list = findChildren(targetNode, targetNode['level'])
        # NodeAndChildren = Tree.objects.filter(profile = profile).filter(ul__in = children_list)
        NodeAndChildren = Tree.objects.filter(profile = profile).filter(ul = ul)
        # for a in NodeAndChildren:
        #     print(str(a))
        listWithValues = []


        marker =  NodeAndChildren[0].active
        for object in NodeAndChildren:
            if marker:
                object.__setattr__("active", False)
            else:
                object.__setattr__("active", True)

            object.save()
            a = {'name': object.ul}
            if marker:
                if object.ua == "Активность не выполнена":
                    a['color'] = "#ff4d4d"
                else:
                    a['color'] = "#1a8cff"
            else:
                a['color'] = "#37474f"

            listWithValues.append(a)
            # if value = 0:
        return JsonResponse({ 'node_list': listWithValues })

    else:
        return JsonResponse({ 'error': 'sorry, fuckoff' })


# def findNotActiveChildren(node):
#     marker = node['active']
#     children_list = findChildren(node, node['level'])
#
#     marker =  NodeAndChildren[0].active
#     for object in NodeAndChildren:
#         if marker:
#             object.__setattr__("active", False)
#         else:
#             object.__setattr__("active", True)
#         object.save()
#         # if value = 0:
#     return JsonResponse({ 'not_active_node': children_list })


@csrf_exempt
def vilaviQualification(request):
    if request.method == 'GET':
        query = VilaviFetch.objects.values_list("q")
        res = {"qualifications": []}
        for record in query:
            if record[0] not in res["qualifications"]:
                res["qualifications"].append(record[0])
        print(json.dumps(res))
        return JsonResponse(res)
    else:
        return JsonResponse({})


@csrf_exempt
def vilaviLevel(request):
    if request.method == 'GET':
        query = VilaviFetch.objects.values_list("g")
        res = {"levels": []}
        for record in query:
            if record[0] not in res["levels"]:
                res["levels"].append(record[0])
        res["levels"].sort()
        a = ""
        print(json.dumps(res))
        return JsonResponse(res)
    else:
        return JsonResponse({})


@csrf_exempt
def profileEmailExist(request):
    # print(request.POST.get('username'))
    # return JsonResponse({})
    if request.method == 'POST':
        print(request.POST.get('username'))
        query = Profile.objects.filter(name = request.POST.get('username'))
        print(query)
        if (query.count() == 1) and (query[0].email is not None) and (query[0].email.__len__() > 0):
            return JsonResponse( { 'exist': 1 } )

    return JsonResponse( { 'exist': 0} )


@csrf_exempt
def profileDeactivate(request):
    if request.method == 'POST':
        result = {}
        parent_name = request.POST.get('parent')
        parent = get_object_or_404(Profile, name = parent_name)
        child = request.POST.get('user')
        grandNode = dataForTreeFromTable(forD3 = False, profileObject = parent, onlyActive = False)
        node = findNode(grandNode, parent.user)
        childList = findChildren(node, node['level'])

        if int(child) in childList:
            result['isChild'] = 1
            prof = Profile.objects.get(user = int(child))
            prof.active = not prof.active
            prof.save()
            print(prof.active)
            result['active'] = prof.active
        else:
            result['isChild'] = 0

        return JsonResponse(result)

@csrf_exempt
def profileInfo(request):
    if request.method == "POST":
        result = {}
        attribute = request.POST.get('by')
        if attribute == 'id':
            id = request.POST.get('id')
            obj = get_object_or_404(Profile, user = id)
            result['id'] = obj.user
            result['name'] = obj.name
            result['isAdmin'] = 0
            result['active'] = obj.active
            if int(obj.user) == 909555:
                result['isAdmin'] = 1

        elif attribute == 'name':
            name = request.POST.get('name')
            obj = get_object_or_404(Profile, name = name)
            result['id'] = obj.user
            result['name'] = obj.name
            result['isAdmin'] = 0
            result['active'] = obj.active
            if int(obj.user) == 909555:
                result['isAdmin'] = 1
    return JsonResponse(result)


class ForgetPasswordView(View):
    form_class = ForgetPasswordForm
    template_name = 'web/forget_password.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        forget_form = self.form_class(request.POST)
        email = request.POST.get('email')
        try:
            username = Profile.objects.get(email = email).user
            user = User.objects.get(username = username)
            password = ''.join(
            random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(12))
            user.set_password(password)
            user.save()
            send_emails(email, password, user)
            return render(request, 'web/password_sent.html', {})
        except Profile.DoesNotExist:
            return render(request, self.template_name, {'form': forget_form})

@method_decorator(login_required, name = 'get')
class ReferenceLinksView(View):
    template_name = 'web/reference_links.html'
    isAdmin = False


    def get(self, request):
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        profile = Profile.objects.get(user=request.user)
        profile_id = profile.user
        telegram_link = profile.telegram_name
        # if profile_id == "909555":
        #     profile_id = ""
        return render(request, self.template_name, {
            'username': username,
            'id': profile_id,
            'tn': telegram_link,
            'isAdmin': self.isAdmin,
        })

def findChildren(node, baseLevel):
    children = []
    children.append(node['name'])

    # print("LLLLLLLLLLLLLEEEEEEEEEEEEEEEEEVVVVVVVVVVVVVVEEEEEEEEEEEEELLLLLLLLLLLLL")
    # print(node["level"])
    if node["level"] == 0:
        node["level"] = node["level"] - (1+baseLevel)
    else:
        node["level"] = node["level"] - baseLevel
    # print(node["level"])

    if 'children' in node:
        if node['children'].__len__() > 0:
            for child in node['children']:
                chilist = findChildren(child, baseLevel)
                for a in chilist:
                    if a not in children:
                        children.append(a)
    return children

def findNode(node, target):
    # print(node['name'])
    # print(type(node['name']))
    # print(target)
    # print(type(target))
    print('[NOE]', node)
    if not node.get('name', None):
        return None
    if str(node['name']) == target:
        print("here")
        return node
    if ('children' in node) and (node['children'].__len__() > 0):
        for child in node['children']:
            n = findNode(child, target)
            if n:
                print("there")
                return n
    print("over there")
    return None



class TreeView(View):
    template_name = 'web/tree.html'
    form_class = FilterForm
    isAdmin = False

    def get(self, request):
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        form = self.form_class(None)

        profile = Profile.objects.get(user = request.user)
        grandNode = dataForTreeFromTable(forD3=False, profileObject = profile, onlyActive=False) # tree from 909555
        vilIdOfNode = Profile.objects.get(user = request.user.username).user # id of the user
        # print("NAAAAAAAAAAAAAAAAAAAAAAAAAAAAAME")
        # print(grandNode['children'][0]['name'])

        node = findNode(grandNode, vilIdOfNode) # find tree node of the user

        # print(json.dumps(grandNode, indent=4))
        if node is None:
            return render(request, self.template_name, {
                'id': profile.user,
                'people': [],
                'username': username,
                'filtering': 'filtering',
                'fform': form,
                'baseLevel': None,
                'isAdmin': self.isAdmin,
            })
        baseLevel = node['level']

        children_list = findChildren(node, baseLevel=baseLevel) # get children of the vilavi_guy


        tree_table = Tree.objects.filter(profile = profile).filter(ul__in=children_list).order_by('sid', 'q')



        return render(request, self.template_name, {
            'id': profile.user,
            'people': tree_table,
            'username': username,
            'filtering': 'filtering',
            'fform': form,
            'baseLevel': baseLevel,
            'isAdmin': self.isAdmin,
        })

    def post(self, request):
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        form = self.form_class(None)

        profile = Profile.objects.get(user=request.user)
        grandNode = dataForTreeFromTable(forD3=False, profileObject = profile, onlyActive=False)  # tree from 909555
        vilIdOfNode = Profile.objects.get(user=request.user.username).user  # id of the user
        node = findNode(grandNode, vilIdOfNode)  # find tree node of the user
        baseLevel = node['level']

        children_list = findChildren(node, baseLevel=baseLevel)  # get children of the vilavi_guy



        res = Tree.objects.allInOne(json.loads(request.POST['all_dict']))
        res = res.filter(profile = profile).filter(ul__in = children_list)
        res = res.order_by('sid', 'q')


        return render(request, self.template_name, {
            'id': profile.user,
            'people': res,
            'username': username,
            'filtering': 'filtering',
            'fform': form,
            'all_dict': json.loads(request.POST['all_dict']),
            'baseLevel': baseLevel,
            'isAdmin': self.isAdmin,
        })


# def dataForTree():
#     resultArray = []
#     with open('tree', 'r') as f:
#         raw = f.read()
#         f.close()
#
#     rows = raw.split('\n')[1:]  # taking of the header
#     data = []
#     for row in rows:
#         cols = row.split(',')
#         if cols.__len__() == 14:
#
#             if cols[12] == 'True':
#                 cols[12] = True
#             else:
#                 cols[12] = False
#
#             if cols[1].__len__() == 0:
#                 cols[1] = None
#             else:
#                 cols[1] = int(cols[1])
#             active = VilaviFetch.objects.get(un=cols[7]).active
#             activity = VilaviFetch.objects.get(un=cols[7]) in VilaviFetch.objects.filter_activity(True)
#
#             if active:
#                 if activity:
#                     ncolor = "#1a8cff"
#                     color = "#1a8cff"
#                 else:
#                     ncolor = "#ff4d4d"
#                     color = "#ff4d4d"
#
#             else:
#                 ncolor = "#37474f"
#                 color = "#37474f"
#
#             # a = {
#             #     "uid" : int(cols[0]),
#             #     "sid" : cols[1],
#             #     "gpv" : int(cols[2]),
#             #     "r" : int(cols[3]),
#             #     "q" : cols[4],
#             #     "g" : int(cols[5]),
#             #     "ul" : int(cols[6]),
#             #     "un" : cols[7],
#             #     "up" : int(cols[8]),
#             #     "ua" : cols[9],
#             #     "uas" : cols[10],
#             #     "uav" : cols[11],
#             #     "dd" : cols[12],
#             #     "actitve": True
#             # }
#             a = {
#                 "id": int(cols[0]),
#                 "pid": cols[1],
#                 "name": cols[6],
#                 "level": cols[5],
#                 "active": active,  # color of parent connection and text
#                 "activity": activity,  # color of inner and outer circle
#                 "number_of_show": 0,
#                 "last_time_show": timezone.now().__str__()[:19],
#                 # "myid": int(cols[5])
#                 # "size": int(cols[0]),
#
#             }
#             data.append(a)
#
#     out = {
#         # 'root': {'id': data[0]["id"], 'parent_id': data[0]["pid"], 'name': data[0]["name"], 'sub': []}
#     }
#
#     for p in data:
#         pid = p['pid'] or 'root'
#         out.setdefault(pid, {'children': []})
#         out.setdefault(p['id'], {'children': []})
#         out[p['id']].update(p)
#         out[pid]['children'].append(out[p['id']])
#     test = out['root']['children'][0]
#
#     def lookForNull(something):
#         if isinstance(something, dict):
#             if bool(something['children']) is False:
#                 del something['children']
#             else:
#                 lookForNull(something['children'])
#         else:
#             for a in something:
#                 lookForNull(a)
#
#
#     lookForNull(test)
#     print(test)
#         j.write(json.dumps(out['root']['children'], ensure_ascii=False))
#         j.close()
#
#     res = test
#     print("TREE BEGINS")
#     # countChildren(res)
#     # findHeight(res)
#     print("Name    Height   Children     DATE")
#     # print(compareLastTimeShow('2017-10-09 20:50:57'))
#     # print(traverseTree(res))
#     with open('SHITTYTREE', 'w') as f:
#         f.write(json.dumps(res, ensure_ascii=False))
#         f.close()
#     return test

def dataForTreeFromTable(forD3, profileObject, onlyActive):
    data = []
    # rows = VilaviFetch.objects.all()
    print("MYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYPROFILE")
    rows = Tree.objects.filter(profile = profileObject).order_by('g')

    print(rows)

    if onlyActive:
        rows = rows.filter(active = True)

    print(rows.count())


    for row in rows:
        active = row.active

        list_over = Tree.objects.filter_activity(0).filter(profile=profileObject)
        list_norm = Tree.objects.filter_activity(1).filter(profile=profileObject)
        list_under = Tree.objects.filter_activity(2).filter(profile=profileObject)
        if row in list_over:
            activity = 0
        elif row in list_norm:
            activity = 1
        if row in list_under:
            activity = 2

        if active:
            if activity == 0:
                ncolor = "#1a8cff"
                color = "#1a8cff"
            elif activity == 1:
                ncolor = "#53ff1a"
                color = "#53ff1a"
            else:
                ncolor = "#ff4d4d"
                color = "#ff4d4d"


        else:
            ncolor = "#37474f"
            color = "#37474f"


        a = {

            "id": row.uid,
            "pid": row.sid,
            "name": row.ul,
            "level": int(row.g),
            "number_of_show": row.numberOfShow,
            "last_time_show": str(row.lastTimeShow)[:19],
            "belong_to": profileObject.user,

        }
        if forD3:
            a['color'] = color # color of parent connection and text
            a['ncolor'] = ncolor # color of node
            a['fullName'] = row.un
            a['gpv'] = row.gpv
            a['phone'] = row.up
            a['qual'] = row.q
        else:
            a['active'] = row.active # added if tree is not used for d3 diagram construction
        data.append(a)
    # return data

    if data.__len__() != 0:
        data[0]['pid'] = ''  # import if not 909555, will crush otherwise

    print(data)



    out = {
    }

    for p in data:
        pid = p['pid'] or 'root'
        out.setdefault(pid, {'children': []})
        out.setdefault(p['id'], {'children': []})
        out[p['id']].update(p)
        out[pid]['children'].append(out[p['id']])
    # print('OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUTTTTTTTTTTTTTTTTT')
    # print(json.dumps(out, indent=4))

    # print('OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUUTTTTTTTTTTTTTTTTT')
    # tree = out[data['pid']]['children'][0]
    tree = {}
    if out.__len__() != 0:
        tree = out['root']['children'][0]


    def lookForNull(something):
        if something.__len__() == 0:
            return
        if isinstance(something, dict):
            if bool(something['children']) is False:
                del something['children']
            else:
                lookForNull(something['children'])
        else:
            for a in something:
                lookForNull(a)

    lookForNull(tree)
    if 'children' not in tree:
        tree['children'] = []

    return tree


def dataForTreeFromVilavi():
    data = []
    rows = VilaviFetch.objects.all()
    for row in rows:

        a = {

            "id": row.uid,
            "pid": row.sid,
            "name": row.ul,
            "level": int(row.g),
        }

        data.append(a)
    out = {
    }

    for p in data:
        pid = p['pid'] or 'root'
        out.setdefault(pid, {'children': []})
        out.setdefault(p['id'], {'children': []})
        out[p['id']].update(p)
        out[pid]['children'].append(out[p['id']])
    tree = out['root']['children'][0]

    def lookForNull(something):
        if isinstance(something, dict):
            if bool(something['children']) is False:
                del something['children']
            else:
                lookForNull(something['children'])
        else:
            for a in something:
                lookForNull(a)

    lookForNull(tree)
    return tree


class ControlProfiles(View):

    template_name = 'web/profileControl.html'
    isAdmin = False

    # chilist = chilist[1:] # exclude himself
    # print(chilist)

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        if int(request.user.username) == 909555:
            self.isAdmin = True
        if not self.isAdmin:
            return redirect('check_tree_vertical')

        data = dataForTreeFromTable(forD3=False, profileObject = profile, onlyActive = False)
        chilist = findChildren(data, baseLevel=data['level'])
        chilist = chilist[1:]


        username = getProfileName(request)
        profile_list = Profile.objects.filter(user__in=chilist).order_by('name')
        print("PROFILE LIST")
        print(profile_list)
        return render(request, self.template_name, {
            'profiles': profile_list,
            'username': username,
            'isAdmin': self.isAdmin,
        })


class UsefulLinkView(View):
    template_name = 'web/usefulLinks.html'
    isAdmin = False

    def get(self, request):
        usefulLinks = UsefulLink.objects.all()
        username = getProfileName(request)
        if request.user.username == "909555":
            self.isAdmin = True


        return render(request, self.template_name, {
            'links': usefulLinks,
            'username': username,
            'isAdmin': self.isAdmin,
        })

class CreateUsefulLinkView(View):
    template_name = "web/usefulLinksEdit.html"
    class_form = UsefulLinkForm
    isAdmin = False

    def get(self, request):
        form = self.class_form(None)
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        return render(request, self.template_name, {
            'form': form,
            'username': username,
            'type': True,
            'isAdmin': self.isAdmin,
        })

    def post(self, request):
        form = self.class_form(request.POST)
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True
        if form.is_valid():
            form.save()
            return redirect('useful_links')
        else:
            return render(request, self.template_name, {
                'form': form,
                'username': username,
                'isAdmin': self.isAdmin,
            })


class EditUsefulLinkView(View):
    template_name = 'web/usefulLinksEdit.html'
    class_form = UsefulLinkForm
    isAdmin = False

    def get(self, request, pk):
        link = get_object_or_404(UsefulLink, pk=pk)
        form = self.class_form(instance=link)
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        return render(request, self.template_name, {
            'form': form,
            'type': False,
            'username': username,
            'isAdmin': self.isAdmin,
        })

    def post(self, request, pk):
        link = get_object_or_404(UsefulLink, pk=pk)
        form = self.class_form(request.POST, instance=link)
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        if form.is_valid():
            form.save()
            return redirect('useful_links')
        else :
            return render(request, self.template_name, {
                'form': form,
                'username': username,
                'type': False,
                'isAdmin': self.isAdmin,
            })

def delete_link(request,pk):
    UsefulLink.objects.filter(pk=pk).delete()
    return redirect('useful_links')

def traverseTree(node):

    # print('------------------------------------------')
    if node['active'] is True:
        if "children" in node:
            if node['children'].__len__() > 0:
                if node['children'].__len__() == 1:
                    if foundOneNodeWithOneChildren(node):
                        return node
                # node['children'].sort(key=lambda x: (findHeight, countChildren))
                # node['children'].sort(key=lambda item: item['last_time_show'], reverse=True)
                if node['children'].__len__() >= 2:
                    print("UNSOOOOOORTED")
                    for a in node['children']:
                        print(a['name'])
                    print("UNSOOOOOORTED")
                    res = []
                    print("SOOOOOORTED")
                    for a in node['children']:
                        if a['active']:
                            res.append(a)
                    node['children'] = res  # get rid of not active nodes
                    node['children'].sort(key=findHeight)
                    node['children'].sort(key=countChildren)
                    for b in node['children']:
                        print(b['name'])
                    print("SOOOOOORTED")

                    # node['children'].sort(key=lambda item: item['number_of_show'])

                    for child in node['children']:
                        record = traverseTree(child)
                        if record is not None:
                            return record

                # return toShow(node)
            else:
                return toShow(node)

        else:
            return toShow(node)
    else:
        return None

def compareLastTimeShow(lastTimeShow):
    #TRUE IF 10 minutes have passed
    sets = SuperAdminSettings.objects.all()[0]
    now = timezone.now()
    year = int(lastTimeShow[:4])
    month = int(lastTimeShow[5:7])
    day = int(lastTimeShow[8:10])
    hour = int(lastTimeShow[11:13])
    minute = int(lastTimeShow[14:16])
    second = int(lastTimeShow[17:19])
    lts = datetime.datetime(year, month, day, hour, minute, second, tzinfo=pytz.UTC)
    print("NOW: " + str(now))
    print("THEN: " + str(lts))
    difference = now - lts
    print("DIF: " + str(difference.seconds))
    differenceInMin = difference.seconds / 60
    if (differenceInMin > sets.registrationTime):
        return True
    else:
        return False


def toShow(node):
    profile = Profile.objects.get(user = node['belong_to'])
    obj = Tree.objects.filter(profile = profile).get(ul=node['name'])
    print(node['name'])
    print(node['number_of_show'])
    print(node['last_time_show'])



    if node['name'] == int(node['belong_to']):
        if node['children'].__len__() >= 2:
            return None



    if node['number_of_show'] < 2:
        node['number_of_show'] += 1
        obj.numberOfShow = node['number_of_show']
        obj.save()
        if node['number_of_show'] == 2:
            node['last_time_show'] = str(timezone.now())[:19]
            obj.lastTimeShow = timezone.now()
            obj.save()
        return node

    else:
        if compareLastTimeShow(node['last_time_show']):
            node['number_of_show'] = 1
            obj.numberOfShow = node['number_of_show']
            obj.save()
            return node
        else:
            return None


def foundOneNodeWithOneChildren(node):
    if compareLastTimeShow(node['last_time_show']):
        profile = Profile.objects.get(user=node['belong_to'])
        obj = Tree.objects.filter(profile=profile).get(ul=node['name'])
        obj.numberOfShow = 2
        obj.lastTimeShow = timezone.now()
        obj.save()
        return True
    return False

def countChildren(node):
    childrenNum = 0
    if "children" in node:
        res = []
        for a in node['children']:
            if a['active']:
                res.append(a)
        node['children'] = res
        if node['children'].__len__() > 0:
            for child in node['children']:
                childrenNum += 1
                childrenNum += countChildren(child)
    # print(node['name'] + ' has    '+ str(childrenNum) + '    children')
    return childrenNum



def findHeight(node):
    height = 0
    if 'children' in node:
        res = []
        for a in node['children']:
            if a['active']:
                res.append(a)
        node['children'] = res
        if node['children'].__len__() > 0:
            for child in node['children']:
                height = max(height, findHeight(child))
    # print(node['name'] + ' is    '+ str(height+1) + '    level high')
    return height + 1


class FillTreeByProfileView(View):

    def get(self, request):
        targetProfile = Profile.objects.get(user = request.user.username)
        targetTreeTable = Tree.objects.filter(profile = targetProfile)

        source = VilaviFetch.objects.all()
        grandNode = dataForTreeFromVilavi()
        # print(str(grandNode['name']))
        print('[Username]', request.user.username)
        targetNode = findNode(grandNode, request.user.username)
        childrenList = findChildren(targetNode, targetNode['level'])

        recordsToAdd = source.filter(ul__in = childrenList)
        counter = 0

        for record in recordsToAdd:
            if not targetTreeTable.filter(ul = record.ul).exists():
                Tree.objects.create(uid = record.uid,
                                    sid = record.sid,
                                    gpv = record.gpv,
                                    r = record.r,
                                    q = record.q,
                                    g = record.g,
                                    ul = record.ul,
                                    un = record.un,
                                    up = record.up,
                                    ur = record.ur,
                                    ua = record.ua,
                                    uas = record.uas,
                                    uav = record.uav,
                                    dd = record.dd,
                                    active = True,
                                    numberOfShow = 0,
                                    lastTimeShow = timezone.now(),
                                    profile = targetProfile)
                counter+=1


        return redirect('check_tree_vertical')




class CheckTreeView(View):
    isAdmin = False
    LOG_URL = "https://office.vilavi.com/Account/Login?ReturnUrl=%2F"
    URL = "https://office.vilavi.com/Account/Login?returnurl=%2F"
    TREE_URL = "https://office.vilavi.com/Info/GetMlmTree?Generation=All&BcNumber=All&BcSide=All"

    payload = {
        'Login': '909555',
        'Password': 'qBEY07!@#'
    }
    # import os
    # print(os.getcwd())
    def get(self, request):

        profile = Profile.objects.get(user = request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject = profile, onlyActive = False)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)


        return render(request, 'web/check_tree.html', {
        # return render(request, 'web/check_tree_full_screen.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isAdmin': self.isAdmin,
        })


class CheckTreeActiveView(View):
    isAdmin = False

    def get(self, request):

        profile = Profile.objects.get(user = request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject = profile, onlyActive = True)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)


        return render(request, 'web/check_tree.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isAdmin': self.isAdmin,
        })

class CheckTreeFullScreenView(View):

    def get(self, request):

        profile = Profile.objects.get(user = request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject = profile, onlyActive = False)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)



        return render(request, 'web/check_tree_full_screen.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isActive': False,
        })

class CheckTreeActiveFullScreenView(View):

    def get(self, request):

        profile = Profile.objects.get(user = request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject = profile, onlyActive = True)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)



        return render(request, 'web/check_tree_full_screen.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isActive': True,
        })



class CheckTreeVerticalView(View):
    isAdmin = False

    def get(self, request):

        profile = Profile.objects.get(user = request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject = profile, onlyActive = False)
        vil_id = profile.user
        print('[GRAND]', grandNode)
        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)
        print('------------------------')
        print(result)

        # return render(request, 'web/test_tree.html', {
        return render(request, 'web/check_tree_vertical.html', {
        # return render(request, 'web/check_tree.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isVertical': True,
            'isAdmin': self.isAdmin,
        })

class CheckTreeActiveVerticalView(View):
    isAdmin = False

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True

        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject=profile, onlyActive=True)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)
        print('------------------------')
        print(result)

        # return render(request, 'web/test_tree.html', {
        return render(request, 'web/check_tree_vertical.html', {
            # return render(request, 'web/check_tree.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isVertical': True,
            'isAdmin': self.isAdmin,
        })

class CheckTreeFullScreenVerticalView(View):

    def get(self, request):

        profile = Profile.objects.get(user = request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)
        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject = profile, onlyActive = False)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)
        print('------------------------')
        print(result)


        return render(request, 'web/check_tree_full_screen_vertical.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isVertical': True,
            'isActive': False,
        })

class CheckTreeActiveFullScreenVerticalView(View):

    def get(self, request):
        profile = Profile.objects.get(user=request.user)
        # data = VilaviFetch.objects.all().order_by('g')
        username = getProfileName(request)

        isTree = True

        grandNode = dataForTreeFromTable(forD3=True, profileObject=profile, onlyActive=True)
        vil_id = profile.user

        result = findNode(grandNode, vil_id)
        result = json.dumps(result, ensure_ascii=False)
        print('------------------------')
        print(result)

        # return render(request, 'web/test_tree.html', {
        return render(request, 'web/check_tree_full_screen_vertical.html', {
            # return render(request, 'web/check_tree.html', {
            'data': result,
            'username': username,
            'isTree': isTree,
            'isVertical': True,
            'isActive': True,
        })





def fillCities(request):

    f = codecs.open('country.csv', 'r', 'cp1251')
    data = f.read()
    colsc = data.split('\n')[1:]
    cou_dict = {}

    for colc in colsc:
        args = colc.split(';')
        if args.__len__() == 3:
            name = args[2].replace('"', '')
            id = int(args[0].replace('"', ''))
            if id != 10668 and id != 9908 and id != 1894 and id != 2303 and id != 248 and id != 3159:
                print(id)
                print(name)
                res = name.encode('cp1251').decode('cp1251').encode('utf8').decode('utf8').replace('\r', '')
                country = Country.objects.create(name=res)

                cou_dict[id] = country

    c = codecs.open('city.csv', 'r', 'cp1251')
    data_city = c.read()
    cols = data_city.split('\n')[1:]
    counter = 0
    for col in cols:
        args = col.split(';')
        if args.__len__() == 4:
            city = args[3]
            cou_id = int(args[1].replace('"', ''))
            city_name = args[3].replace('"', '')

            if cou_id != 10668 and cou_id != 9908 and cou_id != 1894 and cou_id != 2303 and cou_id != 248 and cou_id != 3159:
                print(cou_dict[cou_id])
                print(city_name)
                res = city_name.encode('cp1251').decode('cp1251').encode('utf8').decode('utf8').replace('\r', '')
                country = cou_dict[cou_id]

                City.objects.create(name=res, country=country)

    return JsonResponse({})



    # Country.objects.create(name='Казахстан')
    # Country.objects.create(name='Россия')
    #
    # testing = []
    # # with open('iSetevik/city', 'r') as c:
    # with open('city', 'r') as c:
    #     data = c.read()
    #     c.close()
    # cities = json.loads(data, encoding='utf-8')['cities']
    # # return JsonResponse({'A': cities})
    # for city in cities:
    #     name = city['name']
    #     cou = city['country']
    #     print(name)
    #     print(cou)
    #     print(cou == "Россия")
    #     print(cou == "Казахстан")
    #     country = Country.objects.get(name=cou)
    #     print(country)
    #     print('---------------------')
    #     City.objects.create(name=name, country=country)


    # f = codecs.open('country.csv', 'r', 'cp1251')
    # data = f.read()
    # colsc = data.split('\n')[1:]
    #
    # for colc in colsc:
    #     args = colc.split(';')
    #     if args.__len__() == 3:
    #         name = args[2].replace('"', '')
    #         id = int(args[0].replace('"', ''))
    #         if id == 10668:
    #             print(id)
    #             print(name)
    #             res = name.encode('cp1251').decode('cp1251').encode('utf8').decode('utf8').replace('\r', '')
    #             country = Country.objects.create(name=res)
    #
    # c = codecs.open('city.csv', 'r', 'cp1251')
    # data_city = c.read()
    # cols = data_city.split('\n')[1:]
    # counter = 0
    # for col in cols:
    #     args = col.split(';')
    #     if args.__len__() == 4:
    #         city = args[3]
    #         end = len(city) - 2
    #         cou_id = int(args[1].replace('"', ''))
    #         city_name = args[3].replace('"', '')
    #
    #         if cou_id == 10668:
    #             # print(cou_id)
    #             print(city_name)
    #             res = city_name.encode('cp1251').decode('cp1251').encode('utf8').decode('utf8').replace('\r', '')
    #
    #             City.objects.create(name=res, country=country)
    #
    # URL_COUNTRY = "https://api.vk.com/method/database.getCountries"
    # URL_CITY = "https://api.vk.com/method/database.getCities"
    # with requests.Session() as c:
    #     body = {'need_all': 0, 'version': 5.68}
    #     data = c.post(URL_COUNTRY, data=body)
    #     data.encoding = 'utf-8'
    #     countries = json.loads(data.text)['response']
    #     print(type(countries))
    #     print(countries)
    #     for country in countries:
    #         print("-----------------------------------")
    #         print(country['title'])
    #         print("-----------------------------------")
    #         if country['title'] == 'Украина' or \
    #                         country['title'] == 'Беларусь' or \
    #                         country['title'] == 'Кыргызстан':
    #             mycountry = Country.objects.create(name=country['title'])
    #             citydata = c.post(URL_CITY, {'country_id': country['cid'], 'code': 'RU', 'need_all': 0})
    #             cities = json.loads(citydata.text)['response']
    #             for city in cities:
    #                 City.objects.create(name=city['title'], country=mycountry)
    #                 print(city['title'])

        # cities = {}
        # cities['cities'] = []
        # records = City.objects.all()
        # with open('city', 'w') as c:
        #     for record in records:
        #         a = {}
        #         a['name'] = record.name
        #         a['country'] = record.country.name
        #         cities['cities'].append(a)
        #     c.write(json.dumps(cities, ensure_ascii=False))
        # print(cities)
        # return JsonResponse(cities)





@login_required
def test(request):
    # with open('SHITTYTREE', 'r') as f:
    #     data = json.loads(f.read())
    #     f.close()
    profile = Profile.objects.get(user = request.user)
    data = dataForTreeFromTable(forD3=False, profileObject = profile, onlyActive=False)
    print(data)
    # if data['children'].__len__() == 0 or data['children'].__len__() == 1:
    #     output = data
    # else:
    output = traverseTree(data)

    # with open('SHITTYTREE', 'w') as f:
    #     f.write(json.dumps(data, ensure_ascii=False))
    #     f.close()
    return JsonResponse(output, safe=False)


@csrf_exempt
def vilaviSponsorId(request):
    print(request.method )
    if request.method == "POST":

        allChildrenDeactivated = False
        profile = get_object_or_404(Profile, user=request.POST.get('id'))
        data = dataForTreeFromTable(forD3=False, profileObject=profile, onlyActive=False)
        if data['children'].__len__() == 0 or data['children'].__len__() == 1:
            output = data
        else:
            if not atLeastOneChildrenIsActive(data):
                return JsonResponse(data['name'], safe=False)
            output = traverseTree(data)
        print("MYMHYMYNYMYMHMHs")
        print(output)
        if output is None:
            output = {'name': ''}

        return JsonResponse(output['name'], safe=False)

def atLeastOneChildrenIsActive(node):
    for a in node['children']:
        if a['active']:
            return True
    return False

@csrf_exempt
def timeRemaining(request):
    if request.method == "POST":

        profile = get_object_or_404(Profile, user=request.POST.get('id'))
        data = Tree.objects.filter(profile=profile)
        sets = SuperAdminSettings.objects.all()[0]
        result = sets.inactiveTime*60 # 10 minutes in seconds
        cur_time = timezone.now()
        for record in data:
            dif = leastTimeLeft(record.lastTimeShow, cur_time)
            if dif < result and dif > 0:
                result = dif
        return JsonResponse({'result': result})

def leastTimeLeft(lastTimeShow, currentTime):
    difference = currentTime - lastTimeShow
    sets = SuperAdminSettings.objects.all()[0]
    print("DIIIIIIIIIIIIIIIIIIIIIIIFFFFFFFFFFFFFFFFFF")
    print(sets.inactiveTime*60)
    print(difference.seconds)
    return (sets.inactiveTime*60) - difference.seconds


class SystemSettingsView(View):
    form_class = SystemSettingsForm
    template_name = 'web/superUserSettings.html'
    isAdmin = False

    def get(self, request):

        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True
        else:
            return redirect('fill_tree_table')

        systemSettings = SuperAdminSettings.objects.all()[0]
        form = self.form_class(instance = systemSettings)



        return render(request, self.template_name, {
            'form': form,
            'username': username,
            'isAdmin': self.isAdmin,
            'problems': systemSettings.problems,
            'date': systemSettings.date,
        })

    def post(self, request):


        username = getProfileName(request)
        if int(request.user.username) == 909555:
            self.isAdmin = True
        else:
            return redirect('fill_tree_table')

        systemSettings = SuperAdminSettings.objects.all()[0]
        form = self.form_class(request.POST, instance = systemSettings)



        if form.is_valid() :


            print(form.cleaned_data.get('crawlEmail'))
            clData = form.cleaned_data
            systemSettings.registrationTime = clData.get('registrationTime')
            systemSettings.inactiveTime = clData.get('inactiveTime')
            systemSettings.crawlEmail = clData.get('crawlEmail')
            systemSettings.crawlPassword = clData.get('crawlPassword')
            systemSettings.save()
            # return JsonResponse(form.cleaned_data, safe=False)
            return redirect(reverse_lazy('system_settings'))

        else:
            return render(request, self.template_name, {
                'form': form,
                'username': username,
                'isAdmin': self.isAdmin,
            })

@csrf_exempt
def getTimerValues(request):
    sets = SuperAdminSettings.objects.all()[0]
    res = {}
    res['registration_time'] = sets.registrationTime
    res['inactive_time'] = sets.inactiveTime
    return JsonResponse(res)


class FillTreeOfAllProfilesView(View):
    def get_client_ip(request):
      x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
      if x_forwarded_for:
          ip = x_forwarded_for.split(',')[0]
      else:
          ip = request.META.get('REMOTE_ADDR')
      return ip
    def get(self, request):
        ip = FillTreeOfAllProfilesView.get_client_ip(request)
        if(ip!='185.22.67.22'):
            return JsonResponse({})
        profiles = Profile.objects.all().exclude()

        for profile in profiles:
            targetTreeTable = Tree.objects.filter(profile = profile)

            source = VilaviFetch.objects.all()
            grandNode = dataForTreeFromVilavi()
            # print(str(grandNode['name']))
            targetNode = findNode(grandNode, profile.user)
            childrenList = findChildren(targetNode, targetNode['level'])


            recordsToAdd = source.filter(ul__in = childrenList)
            counter = 0

            for record in recordsToAdd:
                if not targetTreeTable.filter(ul = record.ul).exists():
                    Tree.objects.create(uid = record.uid,
                                        sid = record.sid,
                                        gpv = record.gpv,
                                        r = record.r,
                                        q = record.q,
                                        g = record.g,
                                        ul = record.ul,
                                        un = record.un,
                                        up = record.up,
                                        ur = record.ur,
                                        ua = record.ua,
                                        uas = record.uas,
                                        uav = record.uav,
                                        dd = record.dd,
                                        active = True,
                                        numberOfShow = 0,
                                        lastTimeShow = timezone.now(),
                                        profile = profile)
                    counter+=1

        return JsonResponse({'ip':ip})
