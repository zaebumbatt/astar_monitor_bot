from django.db import models

from core import models as core_models


class Account(core_models.TimeTrackable):
    name = models.CharField(max_length=100, blank=True, default='')
    display = models.CharField(max_length=100, blank=True, default='')
    address = models.CharField(max_length=100, unique=True)
    balance = models.DecimalField(max_digits=30, decimal_places=5, default=0.0)
    balance_lock = models.DecimalField(max_digits=30, decimal_places=5, default=0.0)

    @property
    def rank(self) -> int:
        return Account.objects.filter(balance__gte=self.balance).count()

    @property
    def subscan_link(self) -> str:
        url = 'https://astar.subscan.io/account/'
        return f"<a href='{url}{self.address}'>{self.__str__()}</a>"

    def __str__(self):
        return (
            self.name
            or self.display
            or self.address
        )

    class Meta:
        db_table = 'account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['-balance']


class Dapp(core_models.TimeTrackable):
    name = models.CharField(max_length=100)
    account = models.OneToOneField(Account, on_delete=models.CASCADE)

    @property
    def portal_link(self) -> str:
        url = 'https://portal.astar.network/astar/dapp-staking/dapp?dapp='
        return f"<a href='{url}{self.account.address}'>{self.name}</a>"

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'dapp'
        verbose_name = 'Dapp'
        verbose_name_plural = 'Dapps'
        ordering = ['name']


class Transfer(core_models.TimeTrackable):
    extrinsic_index = models.CharField(max_length=30, unique=True)
    from_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transfers_from'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transfers_to'
    )
    asset_symbol = models.CharField(max_length=20, blank=True)
    module = models.CharField(max_length=20, blank=True)
    amount = models.DecimalField(max_digits=30, decimal_places=5, default=0.0)
    usd_amount = models.DecimalField(max_digits=30, decimal_places=5, default=0.0)

    def __str__(self):
        return (
            f'From: {self.from_account} '
            f'To: {self.to_account} '
            f'Amount: {self.amount} {self.asset_symbol} ({self.usd_amount} USD)'
        )

    class Meta:
        db_table = 'transfer'
        verbose_name = 'Transfer'
        verbose_name_plural = 'Transfers'
        ordering = ['-created_at']


class TONAccount(core_models.TimeTrackable):
    name = models.CharField(max_length=100, blank=True, default='')
    address = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name or self.address

    class Meta:
        db_table = 'ton_account'
        verbose_name = 'TONAccount'
        verbose_name_plural = 'TONAccounts'
        ordering = ['name']


class TONTransfer(core_models.TimeTrackable):
    hash = models.CharField(max_length=100, unique=True)
    source_address = models.CharField(max_length=100)
    destination_address = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=30, decimal_places=5, default=0.0)

    def __str__(self):
        return self.hash

    class Meta:
        db_table = 'ton_transfer'
        verbose_name = 'TONTransfer'
        verbose_name_plural = 'TONTransfers'
        ordering = ['-created_at']
