from django.contrib.auth.forms import SetPasswordForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import *
from django.contrib.auth import authenticate
from material import Layout, Row, Fieldset
# from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from register import *


my_default_errors = {
    'required': 'Заполните поле',
    'invalid': 'Неверные данные',
    'duplicate_username': 'myMESSAGE'
}

with open('countries.txt', 'r') as f:
    r = [(None, 'Страна проживания')]
    for i in f.readlines():
        t = i.strip()
        r.append((t, t))
    choices = tuple(r)


class ExistingUserCreationForm(forms.ModelForm):
    error_messages = {
        'required': 'Заполните поле',
        'invalid': 'Неверные данные',
        'duplicate_username': 'Пользователь с таким id уже существует'
    }

    username = forms.CharField(
        label='Ваш vilavi id',
        required=True,
        error_messages=my_default_errors
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label='Пароль',
        error_messages = my_default_errors
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label='Подтвердить пароль',
        error_messages = my_default_errors
    )

    class Meta:
        model = User
        fields = ('username', 'password', 'confirm_password')

    def clean_username(self):
        username = self.cleaned_data['username']

        if username.__len__() != 6 and not username.isdigit():
            raise forms.ValidationError("Ваш vilavi id должен содержать 6 цифр",
                                        code='username_length')
        else:
            if VilaviFetch.objects.filter(ul=username).count() == 0:
                raise forms.ValidationError("Этот vilavi id не зарегистрирован", code='not_exist_inVilaviFetch')

        try:
            User._default_manager.get(username=username)

            raise forms.ValidationError(self.error_messages['duplicate_username'],
                                        code='duplicate_username')
        except User.DoesNotExist:
            return username

    def clean(self):
        cleaned_data = super(UserCreationForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Пароли не совпадают"
            )


class UserCreationForm(forms.ModelForm):
    error_messages = {
        'required': 'Заполните поле',
        'invalid': 'Неверные данные',
        'duplicate_username': 'Пользователь с таким id уже существует'
    }

    country = forms.ChoiceField(required=True,
                                label='Страна',
                                choices=choices,
                                error_messages=my_default_errors)

    name = forms.CharField(
        label='Имя',
        required=True,
        error_messages=my_default_errors
    )

    surname = forms.CharField(
        label='Фамилия',
        required=True,
        error_messages=my_default_errors
    )

    fathers_name = forms.CharField(
        label='Отчество',
        required=False,
        error_messages=my_default_errors
    )

    def validate_password(value):
        if not re.search(r'\d', value) or not re.search(r'[a-zA-Z]', value):
            raise forms.ValidationError(
                "Пароль должен содержать хотя бы одну цифру и один символ"
            )
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label='Пароль',
        error_messages = my_default_errors,
        validators=[validate_password],
        min_length=6,
    )

    gender = forms.ChoiceField(required=True,
                               label='Пол',
                               choices=(('Male', 'Мужской'), ('Female', 'Женский')))

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label='Подтвердить пароль',
        error_messages = my_default_errors
    )

    email = forms.CharField(
        widget=forms.EmailInput,
        required=True,
        label='Адрес электронной почты',
        error_messages=my_default_errors
    )

    phone = forms.CharField(
        widget=forms.NumberInput,
        required=True,
        label='Телефон',
        error_messages=my_default_errors,
        max_length=11,
        min_length=11,
    )

    agree = forms.BooleanField(
        required=True,
        label="""Я согласен с """,
        error_messages=my_default_errors
    )

    sponsor_id = forms.CharField(
        widget=forms.HiddenInput(),
        required=True,
    )

    class Meta:
        model = User
        fields = ('name', 'surname', 'fathers_name', 'gender', 'country', 'password', 'confirm_password', 'email', 'phone')

    def clean_username(self):
        username = self.cleaned_data['username']

        if username.__len__() != 6 and not username.isdigit():
            raise forms.ValidationError("Ваш vilavi id должен содержать 6 цифр",
                                        code='username_length')
        else:
            if VilaviFetch.objects.filter(ul=username).count() == 0:
                raise forms.ValidationError("Этот vilavi id не зарегистрирован", code='not_exist_inVilaviFetch')

        try:
            User._default_manager.get(username=username)

            raise forms.ValidationError(self.error_messages['duplicate_username'],
                                        code='duplicate_username')
        except User.DoesNotExist:
            return username

    def clean(self):
        cleaned_data = super(UserCreationForm, self).clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError(
                "Пароли не совпадают"
            )


    def save(self, commit=True):
        print(self.cleaned_data)
        data = {
            "IsResident": False,
            "SponsorId": self.cleaned_data['sponsor_id'],
            "FullName": "%s %s" % (self.cleaned_data['name'], self.cleaned_data['surname']),
            "LastName": self.cleaned_data['surname'],
            "FirstName": self.cleaned_data['name'],
            "MiddleName": self.cleaned_data['fathers_name'],
            "Password": self.cleaned_data['password'],
            "ConfirmPassword": self.cleaned_data['password'],
            "Email": self.cleaned_data['email'],
            "PhoneNumber": '+%s'%(self.cleaned_data['phone']),
            "__RequestVerificationToken": "",
            "Agree": True,
            "Gender": self.cleaned_data['gender'],
        }
        vilavi_id = validateVilavi(data)
        print('[ID]', vilavi_id)
        self.cleaned_data['username'] = vilavi_id
        self.instance.username = vilavi_id
        return super(UserCreationForm, self).save()


# class UserAuthenticationForm(forms.ModelForm):
class UserAuthenticationForm(forms.Form):
    error_messages = {
        'required': 'Заполните поле',
        'invalid': 'Неверные данные',
        'duplicate_username': 'Пользователь с таким id уже существует'
    }

    username = forms.IntegerField(
        label='Ваш vilavi id',
        required=True,
        error_messages = my_default_errors
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        required=True,
        label='Пароль',
        error_messages = my_default_errors
    )

    # class Meta:
    #     model = User
    #     fields = ('username', 'password')

    # def clean(self):
    #     cleaned_data = super(UserAuthenticationForm, self).clean()
    #     username = cleaned_data['username']
    #     loguser = Profile.objects.filter(username)
    #
    #     if loguser.count() == 1:
    #         if not loguser[0].active:
    #             raise forms.ValidationError("Ваш аккаунт заблокирован, свяжитесь с вашим куратором!")

    def clean_username(self):
        data = self.cleaned_data['username']
        profile = Profile.objects.filter(user=data)

        if str(data).__len__() != 6:
            raise forms.ValidationError("Ваш vilavi id должен содержать 6 цифр!",
                                        code='username_length')


        if profile.count() == 1:
            if not Profile.objects.get(user=data).active:
                raise forms.ValidationError("Ваш аккаунт заблокирован, свяжитесь с вашим куратором!")
        else:
            raise forms.ValidationError("Такого id не существует в системе!")


        return data



    def clean(self):
        cleaned_data = super(UserAuthenticationForm, self).clean()
        password = cleaned_data.get("password")
        username = cleaned_data.get('username')

        if username and password:
            user = User.objects.get(username = username)
            print(username)
            print(password)

            if not user.check_password(password):
                raise forms.ValidationError("Проверьте введенные данные, id или пароль не соответствуют")





class EditProfileForm(forms.ModelForm):
    user = forms.CharField(
        max_length=100,
        required=False,
        error_messages = my_default_errors
    )

    name = forms.CharField(
        label='Имя',
        required=False,
        error_messages = my_default_errors
    )

    phone = forms.CharField(
        label='Телефон',
        required=False,
        error_messages = my_default_errors,
    )

    email = forms.EmailField(
        label='email',
        required=False,
        error_messages = my_default_errors
    )

    # country = forms.ModelChoiceField(
    #     label='Страна',
    #     queryset=Country.objects.all(),
    #     required=False,
    #     error_messages=my_default_errors
    # )
    #
    mycity = forms.CharField(
        label='Город',
        required=False,
        error_messages=my_default_errors,
    )

    vk = forms.CharField(
        label='Vk',
        required=False,
        error_messages = my_default_errors,
    )

    facebook = forms.CharField(
        label='Facebook',
        required=False,
        error_messages = my_default_errors,
    )

    instagram = forms.CharField(
        label='Instagram',
        required=False,
        error_messages = my_default_errors,
    )

    twitter = forms.CharField(
        label='Twitter',
        required=False,
        error_messages = my_default_errors,
    )

    youtube = forms.CharField(
        label='YouTube',
        required=False,
        error_messages = my_default_errors,
    )

    classmate = forms.CharField(
        label='Одноклассники',
        required=False,
        error_messages=my_default_errors,
    )
    telegram_name = forms.CharField(
        label = 'Telegram',
        required=False,
        error_messages=my_default_errors
    )


    layout = Layout(
        Row('name'),
        Row('phone', 'email'),
        Row('mycity'),
        Fieldset('Социальные сети',
                 'telegram_name','vk', 'facebook',
                 'instagram', 'twitter', 'youtube', 'classmate'
        ),
    )



    class Meta:
        model = Profile
        fields = ('user', 'name', 'phone', 'email','telegram_name',
                  'vk', 'facebook', 'instagram', 'twitter', 'youtube', 'classmate')


    # def clean(self):
    #     cleaned_data = super(EditProfileForm, self).clean()
    #     try:
    #         city = City.objects.get(name=self.__getitem__("mycity").value())
    #     except City.DoesNotExist:
    #         print("VALIDATION")
    #         raise forms.ValidationError(
    #                 "Fuck ZEah"
    #         )


    def clean_mycity(self):
        # city = City.objects.get(name=self.__getitem__("mycity").value())
        # print(city)
        city = City.objects.filter(name=self.__getitem__("mycity").value()).count()

        if city == 0:
            print(city == 0)
            raise forms.ValidationError("Такого Города не существует", code="city_doesnot_exist")
        return self.__getitem__('mycity')
        # username = self.cleaned_data['username']
        #
        # if username.__len__() != 6 and not username.isdigit():
        #     raise forms.ValidationError("Ваш vilavi id должен содержать 6 цифр",
        #                                 code='username_length')
        # else:
        #     try:
        #         User._default_manager.get(username=username)
        #
        #         raise forms.ValidationError("Проверьте vilavi id или пароль",
        #                                     code='no_username')
        #     except User.DoesNotExist:
        #         return username
        #
        #     if VilaviFetch.objects.filter(un=username).count() == 0:
        #         raise forms.ValidationError("Этот vilavi id не зарегистрирован", code='not_exist_inVilaviFetch')


class EditUserForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Имя',
        required=False,
        error_messages = my_default_errors
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=False,
        error_messages = my_default_errors
    )

    layout = Layout(Row('first_name', 'last_name'))

    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class ForgetPasswordForm(forms.ModelForm):
    email = forms.EmailField(
        label = 'Email',
        required = True,
        error_messages = my_default_errors
    )


    class Meta:
        model = Profile
        fields = ('email',)

    def clean(self):
        cleaned_data = super(ForgetPasswordForm, self).clean()
        email = cleaned_data.get('email')

        try:
            user = Profile.objects.get(email = email).user
            return
        except Profile.DoesNotExist:
            raise forms.ValidationError("Такого пользователя не существует")



class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(label=u'Текущий Пароль',
                                       widget=forms.PasswordInput(render_value=False),
                                       error_messages=my_default_errors)
    new_password = forms.CharField(label=u'Новый Пароль',
                                   widget=forms.PasswordInput(render_value=False),
                                   error_messages=my_default_errors)
    retyped_password = forms.CharField(label=u'Подтвердить Пароль',
                                       widget=forms.PasswordInput(render_value=False),
                                       error_messages=my_default_errors)

    def __init__(self, data=None, user=None, *args, **kwargs):
        self.user = user
        super(PasswordChangeForm, self).__init__(data=data, *args, **kwargs)


    def clean_current_password(self):
        cleaned_data = self.cleaned_data
        current_password = cleaned_data.get('current_password', '')


        if not self.user.check_password(current_password):
            raise forms.ValidationError('Текущий пароль не соответствует.')

        return current_password

    def clean(self):
        cleaned_data = self.cleaned_data
        new_password = cleaned_data.get('new_password', '')
        retyped_password = cleaned_data.get('retyped_password', '')

        if len(new_password) == 0 or len(retyped_password) == 0:
            raise forms.ValidationError('Пустые поля пароля')

        if new_password != retyped_password:
            raise forms.ValidationError('Новый Пароль и Подтверждение не совпадают')


        return cleaned_data


class FilterForm(forms.Form):
    name = forms.HiddenInput()
    qualification = forms.HiddenInput()
    level = forms.HiddenInput()
    acitivity = forms.HiddenInput()
    active = forms.HiddenInput()

class UsefulLinkForm(forms.ModelForm):
    name = forms.CharField(
        label='Название',
        required=True,
        error_messages=my_default_errors
    )
    url = forms.URLField(
        label='Ссылка',
        required=True,
        error_messages=my_default_errors
    )


    class Meta:
        model = UsefulLink
        fields = ('name', 'url')



class SystemSettingsForm(forms.ModelForm):
    registrationTime = forms.IntegerField(
        label='Время на регистрацию',
        required=True,
        error_messages=my_default_errors,
    )
    inactiveTime = forms.IntegerField(
        label='Время на отключение ветви',
        required=True,
        error_messages=my_default_errors,
    )
    crawlEmail = forms.CharField(
        label='Логин',
        required=True,
        error_messages=my_default_errors,
    )
    crawlPassword = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
        required=True,
        error_messages=my_default_errors,
    )

    layout = Layout(
        Row('registrationTime'), Row('inactiveTime'),
        Fieldset("Учетная запись", 'crawlEmail', 'crawlPassword')
    )

    class Meta:

        model = SuperAdminSettings
        fields = ('registrationTime', 'inactiveTime', 'crawlEmail', 'crawlPassword')

    def clean_registrationTime(self):
        cleaned_data = self.cleaned_data
        time = cleaned_data.get('registrationTime')

        if time < 2:
            raise forms.ValidationError("Время для регистрации должно быть не менее 2 минут")
        return time

    def clean_crawlEmail(self):
        cleaned_data = self.cleaned_data
        id = cleaned_data.get('crawlEmail')

        print("CLEAND")
        print(cleaned_data)
        # print(id.isdigit())

        if not id.isdigit():
            print("CLEANED DIGIT")
            raise forms.ValidationError("Ваш логин должен содержать только цифры")

        if id.__len__() != 6:
            print("CLEANED HERE")
            raise forms.ValidationError("Ваш логин должен состоять из 6 цифр")


        return id

