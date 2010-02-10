# -*- coding: utf-8 -*-
from django.core.cache import cache

import nose
from nose.tools import eq_, assert_raises

import test_utils

import amo
from amo.urlresolvers import reverse
from amo.helpers import urlparams
from addons.models import Addon
from browse.views import locale_display_name


def test_locale_display_name():
    def check(locale, english, native):
        actual = locale_display_name(locale)
        eq_(actual, (english, native))

    check('el', 'Greek', u'Ελληνικά')
    check('el-XXX', 'Greek', u'Ελληνικά')
    assert_raises(KeyError, check, 'fake-lang', '', '')


class TestView(test_utils.TestCase):
    fixtures = ['browse/test_views']

    def setUp(self):
        cache.clear()
        url = reverse('browse.language_tools')
        response = self.client.get(url, follow=True)
        self.locales = response.context['locales']

    def test_sorting(self):
        """The locales should be sorted by English display name."""
        displays = [locale.display for lang, locale in self.locales]
        eq_(displays, sorted(displays))

    def test_native_missing_region(self):
        """
        If we had to strip a locale's region to find a display name, we
        append it to the native name for disambiguation.
        """
        el = dict(self.locales)['el-XX']
        assert el.native.endswith(' (el-xx)')

    def test_missing_locale(self):
        """If we don't know about a locale, show the addon name and locale."""
        wa = dict(self.locales)['wa']
        eq_(wa.display, 'Walloon Language Pack (wa)')
        eq_(wa.native, '')

    def test_packs_and_dicts(self):
        ca = dict(self.locales)['ca-valencia']
        eq_(len(ca.dicts), 1)
        eq_(len(ca.packs), 2)


class TestThemes(test_utils.TestCase):
    fixtures = ['base/addons']

    def setUp(self):
        # Make all the add-ons themes.
        for addon in Addon.objects.all():
            addon.type_id = amo.ADDON_THEME
            addon.save()

        self.base_url = reverse('browse.themes')
        self.exp_url = urlparams(self.base_url, experimental=True)

    def test_default_sort(self):
        """Default sort should be by downloads."""
        response = self.client.get(self.base_url)
        eq_(response.context['sorting'], 'downloads')

    def test_experimental(self):
        # Only 3 without experimental.
        response = self.client.get(self.base_url)
        eq_(len(response.context['themes'].object_list), 3)

        response = self.client.get(self.exp_url)
        eq_(len(response.context['themes'].object_list), 4)

    def _get_sort(self, sort):
        response = self.client.get(urlparams(self.exp_url, sort=sort))
        eq_(response.context['sorting'], sort)
        return [a.id for a in response.context['themes'].object_list]

    def test_download_sort(self):
        ids = self._get_sort('downloads')
        eq_(ids, [55, 73, 3615, 7172])

    def test_name_sort(self):
        ids = self._get_sort('name')
        eq_(ids, [55, 3615, 7172, 73])

    def test_date_sort(self):
        raise nose.SkipTest('need to fix the modified TODO')
        ids = self._get_sort('date')
        eq_(ids, [7172, 3615, 55, 73])

    def test_rating_sort(self):
        ids = self._get_sort('rating')
        eq_(ids, [7172, 3615, 55, 73])
