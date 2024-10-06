from django.contrib import admin
from .models import Organization, Employee, Tender, Bid, OrganizationResponsible, Review


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description',
                    'type', 'created_at', 'updated_at')
    search_fields = ('name', 'description')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'first_name', 'last_name',
                    'created_at', 'updated_at')
    search_fields = ('username', 'first_name', 'last_name')


@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'service_type', 'status',
                    'organization', 'creator', 'version', 'createdAt', 'updatedAt')
    search_fields = ('name', 'description', 'service_type')
    list_filter = ('status', 'organization')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'status', 'tender',
                    'organization', 'creator', 'version', 'createdAt', 'updatedAt')
    search_fields = ('name', 'description', 'status')
    list_filter = ('status', 'tender', 'organization')


@admin.register(OrganizationResponsible)
class OrganizationResponsibleAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'user')
    search_fields = ('organization__name', 'user__username')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'bid', 'author_feedback',
                    'user', 'description', 'createdAt')
    search_fields = ('bid', 'author')
