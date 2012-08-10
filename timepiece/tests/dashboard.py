from dateutil.parser import parse as dt_parse
import datetime
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

try:
    from django.utils import timezone
except ImportError:
    from timepiece import timezone

from timepiece.templatetags.timepiece_tags import get_active_hours
from timepiece.tests.base import TimepieceDataTestCase
from timepiece import models as timepiece
from timepiece import utils


class DashboardTestCase(TimepieceDataTestCase):

    def setUp(self):
        super(DashboardTestCase, self).setUp()
        self.unpriveleged_user = User.objects.create_user(
            username='tester',
            password='abc',
            email='email@email.com'
        )
        self.url = reverse('new-dashboard')
        self.text = [u'Clock In', u'Add Entry', u'My Active Entries']
        self.now = timezone.now()
        self.start = self.now.replace(hour=8, minute=0, second=0)
        self.yesterday = self.start - datetime.timedelta(days=1)
        self.tomorrow = self.start + datetime.timedelta(days=1)
        self.client.login(username='user', password='abc')

    def dt_near(self, dt_a, dt_b, tolerance=10):
        return abs((dt_a - dt_b).total_seconds()) < tolerance

    def test_todays_work_limits(self):
        """
        todays_entries includes closed entries from today & open entries only
        """
        first = self.log_time(start=self.start, delta=(2, 0))
        open_entry = self.create_entry({
            'start_time': self.start + datetime.timedelta(hours=4)
        })
        yester_entry = self.log_time(start=self.yesterday, delta=(2, 0))
        tomorrow_entry = self.log_time(start=self.tomorrow, delta=(2, 0))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        entries = response.context['todays_entries']['entries']
        pks = (entry['pk'] for entry in entries)
        self.assertEqual(set(pks), set((first.pk, open_entry.pk)))

    def test_todays_work_formatting(self):
        """todays_entries object lists entry values with formatting"""
        first = self.log_time(start=self.start, delta=(2, 0))
        open_entry = self.create_entry({
            'start_time': self.start + datetime.timedelta(hours=4)
        })
        response = self.client.get(self.url)
        entries = response.context['todays_entries']['entries']
        for entry, rsp_entry in zip((first, open_entry), entries):
            self.assertEqual(rsp_entry['project'], entry.project.name)
            self.assertEqual(rsp_entry['start_time'],
                             entry.start_time.isoformat())
            if not entry.end_time:
                entry.end_time = timezone.now().replace(microsecond=0)
            rsp_start = dt_parse(rsp_entry['start_time'])
            rsp_end = dt_parse(rsp_entry['end_time'])
            # The end time for open_entry was calculated sooner, so we allow a
            # tolerance of 10 seconds.
            self.assertTrue(self.dt_near(rsp_end, entry.end_time))
            self.assertTrue(rsp_entry['hours'],
                            '%.2f' % round(entry.total_hours, 2))

    def test_todays_work_start_end(self):
        """
        todays_entries object supplies the start and end of the first and last
        entries in isoformat
        """
        three_hours = datetime.timedelta(hours=3)
        first = self.log_time(start=self.start, delta=(2, 0))
        middle = self.log_time(start=self.start + three_hours, delta=(2, 0))
        last = self.log_time(start=self.start + three_hours * 2, delta=(2, 0))
        response = self.client.get(self.url)
        start = dt_parse(response.context['todays_entries']['start_time'])
        end = dt_parse(response.context['todays_entries']['end_time'])
        self.assertEqual(start.hour, first.start_time.hour)
        self.assertEqual(end.hour, last.end_time.hour)

#    def test_unpriveleged_user(self):
#        """
#        A regular user should not be able to see what people are
#        working on or timesheet related links
#        """
#        self.client.login(username='tester', password='abc')

#        response = self.client.get(self.url)
#        for text in self.text:
#            self.assertNotContains(response, text)

#    def test_timepiece_user(self):
#        """
#        A timepiece user should be able to see what others are
#        working on as well as timesheet links
#        """
#        self.client.login(username='user', password='abc')

#        response = self.client.get(self.url)
#        for text in self.text:
#            self.assertContains(response, text)
