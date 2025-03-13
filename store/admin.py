# from django.contrib import admin
# from .models import AdminStore

# class AdminStoreAdmin(admin.ModelAdmin):
#     list_display = ('company_name', 'email', 'phone', 'is_approved')
#     list_filter = ('is_approved',)
#     search_fields = ('company_name', 'email')
#     actions = ['approve_selected', 'disapprove_selected']

#     def approve_selected(self, request, queryset):
#         updated = queryset.update(is_approved=True)
#         self.message_user(request, f"{updated} seller(s) approved successfully.")
#     approve_selected.short_description = "Approve selected sellers"

#     def disapprove_selected(self, request, queryset):
#         updated = queryset.update(is_approved=False)
#         self.message_user(request, f"{updated} seller(s) disapproved successfully.")
#     disapprove_selected.short_description = "Disapprove selected sellers"

# admin.site.register(AdminStore, AdminStoreAdmin)

from django.contrib import admin
from .models import Category, Subcategory, Product, AdminStore

# Admin for Category
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    actions = ['activate_selected', 'deactivate_selected']
    
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} category(ies) activated successfully.")
    activate_selected.short_description = "Activate selected categories"
    
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} category(ies) deactivated successfully.")
    deactivate_selected.short_description = "Deactivate selected categories"

# Admin for Subcategory with inline display in Category
class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1
    prepopulated_fields = {'slug': ('name',)}

class SubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'category__name')
    prepopulated_fields = {'slug': ('name',)}
    actions = ['activate_selected', 'deactivate_selected']
    
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} subcategory(ies) activated successfully.")
    activate_selected.short_description = "Activate selected subcategories"
    
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} subcategory(ies) deactivated successfully.")
    deactivate_selected.short_description = "Deactivate selected subcategories"

# Update the Category admin to include Subcategory inline
CategoryAdmin.inlines = [SubcategoryInline]

# Admin for Product
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'subcategory', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('category', 'subcategory', 'is_active')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_selected', 'deactivate_selected']
    
    def activate_selected(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} product(s) activated successfully.")
    activate_selected.short_description = "Activate selected products"
    
    def deactivate_selected(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} product(s) deactivated successfully.")
    deactivate_selected.short_description = "Deactivate selected products"

# Admin for Vendor Management
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

# Register all models with their admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory, SubcategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(AdminStore, AdminStoreAdmin)