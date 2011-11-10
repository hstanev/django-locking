# encoding: utf-8

from datetime import datetime

from django.contrib import admin
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django import forms

from locking import LOCK_TIMEOUT, views
from locking.models import Lock

class LockableAdmin(admin.ModelAdmin):
#     @property
#     class Media:
#         # because reverse() doesn't yet work when this module is first loaded
#         # (the urlconf still has to load at that point) the media definition
#         # has to be dynamic, and we can't simply add a Media class to the
#         # ModelAdmin as you usually would.
#         #
#         # Doing so would result in an ImproperlyConfigured exception, stating
#         # "The included urlconf doesn't have any patterns in it."
#         # 
#         # See http://docs.djangoproject.com/en/dev/topics/forms/media/#media-as-a-dynamic-property
#         # for more information about dynamic media definitions.
#         
#         css = {
#             'all': ('locking/css/locking.css',)
#             }
#         js = (
#             'http://ajax.googleapis.com/ajax/libs/jquery/1.4.2/jquery.min.js', 
#             'locking/js/jquery.url.packed.js',
#             #reverse('django.views.i18n.javascript_catalog'),
#             #reverse('locking_variables'),
#             'locking/js/admin.locking.js',
#             )
        
        #return forms.Media(css=css, js=js)
    
    def changelist_view(self, request, extra_context=None):
        # we need the request objects in a few places where it's usually not present, 
        # so we're tacking it on to the LockableAdmin class
        self.request = request
        return super(LockableAdmin, self).changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        # object creation doesn't need/have locking in place
        if obj.pk:
            obj.unlock_for(request.user)
        obj.save()
        
    def lock(self, obj):
        if obj.is_locked:
            seconds_remaining = obj.lock_seconds_remaining
            minutes_remaining = seconds_remaining/60
            locked_until = _("Still locked for %s minutes by %s") \
                % (minutes_remaining, obj.locked_by)
            if self.request.user == obj.locked_by: 
                locked_until_self = _("You have a lock on this article for %s more minutes.") \
                    % (minutes_remaining)
                return '<img src="%slocking/img/page_edit.png" title="%s" />' \
                    % (settings.MEDIA_URL, locked_until_self)
            else:
                locked_until = _("Still locked for %s minutes by %s") \
                    % (minutes_remaining, obj.locked_by)
                return '<img src="%slocking/img/lock.png" title="%s" />' \
                    % (settings.MEDIA_URL, locked_until)

        else:
            return ''
    lock.allow_tags = True
    
    list_display = ('__str__', 'lock')


def get_lock_for_admin(self_obj, obj):
	''' 
	returns the locking status along with a nice icon for the admin interface 
	use in admin list display like so: list_display = ['title', 'get_lock_for_admin']
	'''
	
	locked_by = ''
	try:
		lock = Lock.objects.get(entry_id=obj.id, app=obj.__module__[0:obj.__module__.find('.')], model=obj.__class__.__name__.lower())
		class_name = 'locked'
		locked_by = lock.locked_by.display_name
	except Lock.DoesNotExist:
		class_name = 'unlocked'
	
	img_path = 	settings.ADMIN_MEDIA_PREFIX + 'blog/img/'
	
	output = str(obj.id)
	
	if self_obj.request.user.has_perm(u'blog.unlock_post'): 
	
		return '<a href="#" class="lock-status ' + class_name + '" title="Locked By: ' + locked_by + '" >' + output  + '</a>'
	else: 
		return '<span class="lock-status ' + class_name + '" title="Locked By: ' + locked_by + '">' + output  + '</span><!-- ' + __module__[0:obj.__module__.find('.')] + ' -- ' + obj.id + ' -- ' + obj.__class__.__name__.lower()) + ' -- ' + lock.locked_by.display_name + ' -->'
		
get_lock_for_admin.allow_tags = True
get_lock_for_admin.short_description = 'Lock'
