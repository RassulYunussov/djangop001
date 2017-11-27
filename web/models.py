from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

class ProfileManager(models.Manager):
    use_for_related_fields = True

    def filter_exists(self, id):
        obj = super(ProfileManager, self).get_queryset().filter(user = str(id))
        if obj:
            return True
        else:
            return False

class CustomManager(models.Manager):
    use_for_related_fields = True


    def filter_exists(self, id):
        obj = super(CustomManager, self).get_queryset().filter(ul = str(id))
        print(obj)
        return obj

    def filter_qualification(self, items):
        return super(CustomManager, self).get_queryset().filter(q__in = items)

    def filter_level(self, items):
        return super(CustomManager, self).get_queryset().filter(g__in = items)

    def filter_activity(self, item):
        if item == 0:
            res = super(CustomManager, self).get_queryset().filter(ua__exact = "Бонусная активность выполнена")
        elif item == 1:
            res = super(CustomManager, self).get_queryset().filter(ua__exact = "Накопительная активность выполнена")
        else:
            res = super(CustomManager, self).get_queryset().filter(ua__exact="Активность не выполнена")

        return res

    def filter_active(self, item):
        return super(CustomManager, self).get_queryset().filter(active=item)

    def allInOne(self, items, **kwargs):
        print("items in allInOne")
        result = super(CustomManager, self).get_queryset()
        if "name" in items:
            if items["name"]:
                print(items["name"])
                result = result.filter(un__icontains = items["name"])
        #     # print("name")
        #     # print(result)

        if "gpv" in items:
            sign = items["gpv"]["sign"]
            value = items["gpv"]["value"]
            if len(value) == 0:
                value = 0
            else :
                value = int(value)
            print("VALUE - " + str(value))

            if sign == "000":
                # print("INSIDE 000")
                pass
            elif sign == "001":
                # print("INSIDE 001")
                result = result.filter(gpv__lte = value)
            elif sign == "010":
                # print("INSIDE 010")
                result = result.filter(gpv = value)
            # elif sign == "011":
            #     # print("INSIDE 011")
            #     result = result.filter(gpv__lte = value)
            elif sign == "100":
                # print("INSIDE 100")
                result = result.filter(gpv__gte = value)
            # elif sign == "101":
            #     # print("INSIDE 101")
            #     result = result.exclude(gpv = value)
            # elif sign == "110":
            #     # print("INSIDE 110")
            #     result = result.filter(gpv__gte = value)
            # elif sign == "111":
            #     # print("INSIDE 111")
            #     pass
            else:
                pass

            # print("gpv")
            # print(result)

        if "active" in items:
            if items["active"] == "01":
                # print("INSIDE 01")
                result = result.filter(active = False)
            elif items["active"] == "10":
                # print("INSIDE 10")
                result = result.filter(active = True)
            elif items["active"] == "00":
                # print("INSIDE 00")
                result = result.filter(active = None)
            elif items["active"] == "11":
                # print("INSIDE 11")
                pass
            else:
                # print("INSIDE ELSE")
                pass
            # print("acitve")
            # print(result.values("active"))

        if "qualifications" in items:

            quals = []
            for item in items["qualifications"]:
                quals.append(item["data"])
            # print("QUALIICATIONS")
            # print(quals)
            result = result.filter(q__in = quals)
            print(result)
            # print("qual")
            # print(result)

        if "levels" in items:

            levs = []
            for item in items["levels"]:
                levs.append(item["data"])
            # print("LEVELS")
            # print(levs)
            result = result.filter(g__in = levs)

        #     # print("lvl")
        #     # print(result)

        if "activity" in items:
            print(items["activity"])
            # if items["activity"] == "10":
            #     result = result.filter(ua__exact="Бонусная активность выполнена")
            # elif items["activity"] == "01":
            #     result = result.exclude(ua__exact="Бонусная активность выполнена")
            # elif items["activity"] == "00":
            #     result = result.filter(ua = None)
            # elif items["activity"] == "11":
            #     pass
            # else:
            #     pass

            if items["activity"] == "000":
                result = result.filter(ua=None)
            elif items["activity"] == "001":
                result = result.filter(ua__exact="Активность не выполнена")
            elif items["activity"] == "010":
                result = result.filter(ua__exact="Накопительная активность выполнена")
            elif items["activity"] == "011":
                result = result.filter(ua__in=["Активность не выполнена", "Накопительная активность выполнена"])
            elif items["activity"] == "100":
                result = result.filter(ua__exact="Бонусная активность выполнена")
            elif items["activity"] == "101":
                result = result.filter(ua__in=["Бонусная активность выполнена", "Активность не выполнена"])
            elif items["activity"] == "110":
                result = result.filter(ua__in=["Бонусная активность выполнена", "Накопительная активность выполнена"])
            elif items["activity"] == "111":
                pass
            else:
                pass



            # print("acitvity")
            # print(result)

        # print("GRAND")
        # print(result)
        return result


class Profile(models.Model):
    user = models.CharField(max_length=6, blank=True, null=True)
    name = models.CharField(max_length=128)
    phone = models.CharField(default="", max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=128, blank=True, null=True)
    country = models.ForeignKey('Country', blank=True, null=True)
    city = models.ForeignKey('City', blank=True, null=True)
    vk = models.TextField(default="", blank=True, null=True)
    facebook = models.TextField(default="", blank=True, null=True)
    instagram = models.TextField(default="", blank=True, null=True)
    twitter = models.TextField(default="", blank=True, null=True)
    youtube = models.TextField(default="", blank=True, null=True)
    classmate = models.TextField(default="", blank=True, null=True)
    telegram_name = models.CharField(default="", max_length=64, blank=True, null=True)
    register_date = models.DateTimeField(default=timezone.now())
    active = models.BooleanField(default=True)

    objects = ProfileManager()




class VilaviFetch(models.Model):
    uid = models.IntegerField(blank=False)
    sid = models.IntegerField(blank=True, null=True)
    gpv = models.IntegerField(blank=False)
    r = models.CharField(max_length=30, blank=False)
    q = models.CharField(max_length=30, blank=False)
    g = models.IntegerField(blank=False)
    ul = models.IntegerField(blank=False)
    un = models.CharField(max_length=256, blank=False)
    up = models.CharField(max_length=20, blank=False)
    ur = models.CharField(default="", max_length=30, blank=False)
    ua = models.CharField(max_length=50, blank=False)
    uas = models.CharField(max_length=30)
    uav = models.CharField(max_length=50)
    dd = models.BooleanField(blank=True)

    objects = CustomManager()

class UsefulLink(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)
    url = models.URLField(max_length=200, blank=False, null=False)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=100, blank=False)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=100, blank=False)
    country = models.ForeignKey('Country')

    def __str__(self):
        return self.name

class Tree(models.Model):
    uid = models.IntegerField(blank=False)
    sid = models.IntegerField(blank=True, null=True)
    gpv = models.IntegerField(blank=False)
    r = models.CharField(max_length=30, blank=False)
    q = models.CharField(max_length=30, blank=False)
    g = models.IntegerField(blank=False)
    ul = models.IntegerField(blank=False)
    un = models.CharField(max_length=256, blank=False)
    up = models.CharField(max_length=20, blank=False)
    ur = models.CharField(default="", max_length=30, blank=False)
    ua = models.CharField(max_length=50, blank=False)
    uas = models.CharField(max_length=30)
    uav = models.CharField(max_length=50)
    dd = models.BooleanField(blank=True)
    active = models.BooleanField(default=True, blank=False)
    numberOfShow = models.IntegerField(default=0, blank=False)
    lastTimeShow = models.DateTimeField(default=timezone.now())
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    objects = CustomManager()

    def __str__(self):
        return str(self.ul) + ' to ' + self.profile.name

class PreVilaviFetch(models.Model):
    uid = models.IntegerField(blank=False)
    sid = models.IntegerField(blank=True, null=True)
    gpv = models.IntegerField(blank=False)
    r = models.CharField(max_length=30, blank=False)
    q = models.CharField(max_length=30, blank=False)
    g = models.IntegerField(blank=False)
    ul = models.IntegerField(blank=False)
    un = models.CharField(max_length=256, blank=False)
    up = models.CharField(max_length=20, blank=False)
    ur = models.CharField(default="", max_length=30, blank=False)
    ua = models.CharField(max_length=50, blank=False)
    uas = models.CharField(max_length=30)
    uav = models.CharField(max_length=50)
    dd = models.BooleanField(blank=True)

    def __str__(self):
        return str(self.ul)


class SuperAdminSettings(models.Model):
    registrationTime = models.IntegerField(blank=False, default=10)
    inactiveTime = models.IntegerField(blank=False, default=10)
    crawlEmail = models.CharField(max_length=128)
    crawlPassword = models.CharField(max_length=128)
    problems = models.BooleanField()
    date = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return str(self.crawlEmail) + " " + str(self.crawlPassword)


