from django.contrib import admin

from .models import Comment, Post, Tag

# Register your models here.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    list_filter = ('tags',)
    filter_horizontal = ('tags',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


admin.site.register(Comment)