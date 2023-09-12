from django.contrib import admin

from iam import models as iam_models


@admin.register(iam_models.CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    pass
