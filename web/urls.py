from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^myroom/$', views.personal_area, name='personal_area'),
    url(r'^registration/$', views.UserFormView.as_view(), name='user_registration'),
    url(r'^registration_existing/$', views.ExistingUserFormView.as_view(), name='registration_existing'),
    url(r'^login/$', views.UserSignFormView.as_view(), name='user_authentication'),
    url(r'^logout/$', views.logout_view, name='logout'),
    url(r'^fill_tree_table/$', views.FillTreeByProfileView.as_view(), name='fill_tree_table'),
    url(r'^fill_all_tree/$', views.FillTreeOfAllProfilesView.as_view(), name='fill_all_tree'),
    url(r'^myroom/edit_profile/((?P<pk>\d+)/)?$', views.EditProfileView.as_view(), name='edit_profile'),
    url(r'^myroom/reference_links/$', views.ReferenceLinksView.as_view(), name='reference_links'),
    url(r'^myroom/system_settings/$', views.SystemSettingsView.as_view(), name='system_settings'),

    url(r'^myroom/profile_control/$', views.ControlProfiles.as_view(), name='control_profile'),

    url(r'^myroom/useful_links/$', views.UsefulLinkView.as_view(), name='useful_links'),
    url(r'^myroom/useful_links/create/$', views.CreateUsefulLinkView.as_view(), name='useful_link_create'),
    url(r'^myroom/useful_links/edit/(?P<pk>\d+)/$', views.EditUsefulLinkView.as_view(), name='useful_link_edit'),
    url(r'^myroom/useful_links/delete/(?P<pk>\d+)/$', views.delete_link, name='useful_link_delete'),

    url(r'^myroom/change_password/$', views.PasswordChangeView.as_view(), name='change_password'),

    url(r'^myroom/tree/$', views.TreeView.as_view(), name='tree'),
    url(r'^myroom/check_tree/$', views.CheckTreeView.as_view(), name='check_tree'),
    url(r'^myroom/check_tree/active/$', views.CheckTreeActiveView.as_view(), name='check_tree_active'),
    url(r'^myroom/check_tree/full_screen$', views.CheckTreeFullScreenView.as_view(), name='check_tree_fs'),
    url(r'^myroom/check_tree/active/full_screen$', views.CheckTreeActiveFullScreenView.as_view(), name='check_tree_active_fs'),

    url(r'^myroom/check_tree/vertical/$', views.CheckTreeVerticalView.as_view(), name='check_tree_vertical'),
    url(r'^myroom/check_tree/active/vertical/$', views.CheckTreeActiveVerticalView.as_view(), name='check_tree_active_vertical'),
    url(r'^myroom/check_tree/full_screen/vertical/$', views.CheckTreeFullScreenVerticalView.as_view(), name='check_tree_fs_vertical'),
    url(r'^myroom/check_tree/active/full_screen/vertical/$', views.CheckTreeActiveFullScreenVerticalView.as_view(), name='check_tree_active_fs_vertical'),


    url(r'^forget_password/$', views.ForgetPasswordView.as_view(), name='forget_password'),

    url(r'^api/countries/$', views.countryList, name='countries'),
    url(r'^api/cities_by_country/$', views.cityListByCountry, name='cities'),
    url(r'^api/cites/$', views.filterCities, name='filter_cities'),
    url(r'^api/vilavi_activity/$', views.vilaviActivity, name='vilavi_activity'),
    url(r'^api/vilavi_qualifications/$', views.vilaviQualification, name='vilavi_qualifications'),
    url(r'^api/vilavi_level/$', views.vilaviLevel, name='vilavi_level'),
    url(r'^api/vilavi_sponsor_id/$', views.vilaviSponsorId, name='vilavi_sponsor_id'),
    url(r'^api/profile_email_exist/$', views.profileEmailExist, name='profile_email_exist'),
    url(r'^api/profile_deactivate/$', views.profileDeactivate, name='profile_deactivate'),
    url(r'^api/profile_info/$', views.profileInfo, name='profile_info'),
    url(r'^api/time_remaining/$', views.timeRemaining, name='time_remaining'),
    url(r'^api/timer_values/$', views.getTimerValues, name='timer_values'),
    url(r'^test/$', views.test, name='test'),
    # url(r'^fill_cities/$', views.fillCities, name='fill_cities'),
]
