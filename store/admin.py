from django.contrib import admin
from .models import AdminStore

class AdminStoreAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'email', 'phone', 'is_approved')
    list_filter = ('is_approved',)
    search_fields = ('company_name', 'email')
    actions = ['approve_selected', 'disapprove_selected']

    def approve_selected(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} seller(s) approved successfully.")
    approve_selected.short_description = "Approve selected sellers"

    def disapprove_selected(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} seller(s) disapproved successfully.")
    disapprove_selected.short_description = "Disapprove selected sellers"

admin.site.register(AdminStore, AdminStoreAdmin)
