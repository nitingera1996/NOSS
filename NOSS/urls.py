"""NOSS URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import include, url
from django.contrib import admin
import apis.views
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^$', apis.views.index, name='index'),
    url(r'^profile/$', apis.views.profile, name='profile'),
    url(r'^openvpn_password/',apis.views.openvpn_password, name='openvpn_password'),
    url(r'^airroute/$',apis.views.air_route,name='airroute'),
    url(r'^railroute/$',apis.views.rail_route,name='railroute'),
    url(r'^predict_city/$',apis.views.predict_city,name='predict_city'),
    url(r'^predict_city_with_journey/$',apis.views.predict_city_with_journey,name='predict_city_with_journey'),
    url(r'^newtoken/$', apis.views.newtoken, name='newtoken'),
    url(r'^docs/$', apis.views.docs, name='docs'),
    url(r'^faqs/$', apis.views.faqs, name='faqs'),
)
