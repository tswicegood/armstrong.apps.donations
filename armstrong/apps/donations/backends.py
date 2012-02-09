from armstrong.utils.backends import GenericBackend
from authorize import aim
from authorize import arb
from billing import get_gateway
import datetime
from django.conf import settings as django_settings

from . import forms


class AuthorizeNetBackend(object):
    def __init__(self, api_class=None, settings=None):
        if api_class is None:
            api_class = aim.Api
        self.api_class = api_class
        if settings is None:
            settings = django_settings
        self.settings = settings

    def get_api(self):
        return self.api_class(self.settings.AUTHORIZE["LOGIN"],
                self.settings.AUTHORIZE["KEY"], delimiter=u"|")

    def get_recurring_api(self):
        pass

    def get_form_class(self):
        return forms.AuthorizeDonationForm

    def purchase(self, donation, form):
        result = self.onetime_purchase(donation, form)
        if not result["status"]:
            return result
        if donation.donation_type and donation.donation_type.repeat > 0:
            return self.recurring_purchase(donation, form)
        return result

    def recurring_purchase(self, donation, form):
        today = datetime.date.today()
        start_date = u"%s" % ((today + datetime.timedelta(days=30))
                .strftime("%Y-%m-%d"))
        api = self.get_recurring_api()
        data = form.get_data_for_charge(donation.donor, recurring=True)
        data.update({
            "amount": donation.amount,
            "interval_unit": arb.MONTHS_INTERVAL,
            "interval_length": u"1",
            "bill_first_name": u"%s" % donation.donor.name.split(" ")[0],
            "bill_last_name": u"%s" % donation.donor.name.split(" ", 1)[-1],
            "total_occurrences": donation.donation_type.repeat,
            "start_date": start_date,
        })
        api.create_subscription(**data)

    def onetime_purchase(self, donation, form):
        api = self.get_api()
        data = form.get_data_for_charge(donation.donor)
        donor = donation.donor
        data.update({
            "amount": donation.amount,
            "description": u"Donation: $%d" % donation.amount,
            "first_name": unicode(donor.name.split(" ")[0]),
            "last_name": unicode(donor.name.split(" ", 1)[-1]),

            # TODO: extract and be conditional
            "address": donor.address.address,
            "city": donor.address.city,
            "state": donor.address.state,
            "zip": donor.address.zipcode,
        })
        response = api.transaction(**data)
        status = response["reason_code"] == u"1"
        if status:
            donation.processed = True
        return {
            "status": status,
            "reason": response["reason_text"],
            "response": response,
        }


raw_backend = GenericBackend("ARMSTRONG_DONATIONS_BACKEND", defaults=[
    "armstrong.apps.donations.backends.AuthorizeNetBackend",
])

get_backend = raw_backend.get_backend
