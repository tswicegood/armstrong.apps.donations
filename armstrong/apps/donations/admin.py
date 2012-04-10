try:
    from armstrong import hatband as admin
except ImportError:
    from django.contrib import admin

from . import models

admin.stie.register(models.Donation)
admin.site.register(models.Donor)
admin.site.register(models.DonorAddress)
admin.site.register(models.DonationType)
admin.site.register(models.DonationTypeOption)
admin.site.register(models.PromoCode)
