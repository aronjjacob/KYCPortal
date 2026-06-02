from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
	"""Custom User admin with group management and role display."""
    

	list_display = ('username', 'email', 'get_groups', 'is_staff', 'is_active')
	list_filter = ('is_staff', 'is_active', 'groups')
	search_fields = ('username', 'email')
	filter_horizontal = ('groups', 'user_permissions')
    
	def get_groups(self, obj):
		"""Display user's groups/roles."""
		return ', '.join([g.name for g in obj.groups.all()]) or 'No role'
	get_groups.short_description = 'Role(s)'


# Register User with custom admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class GroupAdmin(admin.ModelAdmin):
	"""Admin for Group management."""
	list_display = ('name', 'get_user_count')
	search_fields = ('name',)
	filter_horizontal = ('permissions',)
    
	def get_user_count(self, obj):
		"""Display number of users in this group."""
		return obj.user_set.count()
	get_user_count.short_description = 'User Count'


# Register Group with custom admin
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
