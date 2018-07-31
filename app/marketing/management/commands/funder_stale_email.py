'''
    Copyright (C) 2017 Gitcoin Core

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

'''
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from dashboard.models import Bounty
from marketing.mails import funder_stale


class Command(BaseCommand):

    help = 'solicits feedback from stale funders'

    def add_arguments(self, parser):
        parser.add_argument('days', default=30, type=int)

    def handle(self, *args, **options):
        if settings.DEBUG:
            print("not active in non prod environments")
            return

        # config
        days = options['days']
        if days < 7:
            time_as_str = 'about a week'
        elif days < 27:
            time_as_str = 'a few weeks'
        elif days < 27:
            time_as_str = 'about a month'
        elif days < 90:
            time_as_str = 'a few months'
        else:
            time_as_str = 'quite a bit'

        start_time = timezone.now() - timezone.timedelta(days=(days+1))
        end_time = timezone.now() - timezone.timedelta(days=(days))
        base_bounties = Bounty.objects.filter(
            network='mainnet',
            current_bounty=True,
            )

        candidate_bounties = base_bounties.filter(
            web3_created__gt=start_time,
            web3_created__lt=end_time,
            )

        for bounty in candidate_bounties.distinct('bounty_owner_github_username'):
            handle = bounty.bounty_owner_github_username
            email = bounty.bounty_owner_email

            if not handle:
                continue
                
            print(handle)

            has_posted_in_last_days_days = base_bounties.filter(
                web3_created__gt=end_time,
                bounty_owner_github_username=handle,
                ).exists()

            if not has_posted_in_last_days_days:
                # TODO: do we want to suppress the email if the user 
                # has received this specific email before

                # send the email
                funder_stale(email, handle, days, time_as_str)
            else:
                print(" - has posted recently; not sending")
