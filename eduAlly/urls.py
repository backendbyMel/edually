"""
URL configuration for eduAlly project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name="register"),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name="login"),
    path('logout/',auth_views.LogoutView.as_view(template_name='users/logout.html'),name="logout"),
    path('profile/',user_views.profile, name = "profile"),
    path('school_year/', include('schoolYear.urls')),
    path('term/', include('term.urls')),
    path('dashboard/', user_views.dashboard, name="dashboard"),
    path('', user_views.home, name="home"),
    path('section/', include('sections.urls')),
    path('student/', include('students.urls')),
    path('coming-soon/',user_views.coming_soon,name='coming-soon'),
    path('password/change/',auth_views.PasswordChangeView.as_view(template_name='users/password_change.html',success_url='/password/change/done/'),name='password-change'),
    path('password/change/done/',auth_views.PasswordChangeDoneView.as_view(template_name='users/password_change_done.html'),name='password-change-done'),
    path('password/reset/',auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url='/password/reset/done/'), name='password-reset'),
    path('password/reset/',auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url='/password/reset/done/'),
        name='password-reset'),
    path('password/reset/done/',auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html'),name='password-reset-done'),
    path('password/reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url='/password/reset/complete/'),
        name='password-reset-confirm'),
    path('password/reset/complete/',auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'),name='password-reset-complete'),
    path('username/reset/',user_views.forgot_username, name='forgot-username'),
    path("password/change/",auth_views.PasswordChangeView.as_view(
        template_name="users/password_change.html",
        success_url="/password/change/done/",),
        name="password-change",),
    path("password/change/done/",auth_views.PasswordChangeDoneView.as_view(
        template_name="users/password_change_done.html",),
        name="password-change-done",),
    path("email/change/", user_views.change_email, name="email-change"),
    path("profile/name/change/", user_views.change_name, name="name-change"),
    path('getting-started/', user_views.getting_started, name='getting-started'),
    path('getting-started/done/', user_views.mark_guide_seen, name='mark-guide-seen'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
