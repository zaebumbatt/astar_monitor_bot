from django.contrib import admin

from monitor import models as monitor_models


@admin.register(monitor_models.Account)
class AccountAdmin(admin.ModelAdmin):
    readonly_fields = (
        'display',
        'balance',
        'balance_lock',
    )
    search_fields = ['address']


@admin.register(monitor_models.Dapp)
class DappAdmin(admin.ModelAdmin):
    readonly_fields = (
        'name',
        'account',
    )


@admin.register(monitor_models.Transfer)
class TransferAdmin(admin.ModelAdmin):
    readonly_fields = (
        'extrinsic_index',
        'from_account',
        'to_account',
        'asset_symbol',
        'module',
        'amount',
    )


@admin.register(monitor_models.TONAccount)
class TONAccountAdmin(admin.ModelAdmin):
    search_fields = ['address']
