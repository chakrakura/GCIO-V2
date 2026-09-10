from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from modules.home_page_settings.models import HomePageSettings
from modules.roles.models import Role


class HomePageSettingsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        super_role = Role.objects.get(slug='super-admin')
        admin_role = Role.objects.get(slug='administrator')
        client_role = Role.objects.get(slug='client-user')

        self.super_admin = User.objects.create_user('super', 'super@example.com', 'pass')
        self.super_admin.profile.role = super_role
        self.super_admin.profile.save()

        self.administrator = User.objects.create_user('admin', 'admin@example.com', 'pass')
        self.administrator.profile.role = admin_role
        self.administrator.profile.save()

        self.client_user = User.objects.create_user('client', 'client@example.com', 'pass')
        self.client_user.profile.role = client_role
        self.client_user.profile.save()

    def test_defaults_are_true(self):
        settings_obj = HomePageSettings.load()
        self.assertTrue(settings_obj.show_featured_research)
        self.assertTrue(settings_obj.show_latest_research)
        self.assertTrue(settings_obj.show_weekly_notes)
        self.assertTrue(settings_obj.show_monthly_notes)
        self.assertTrue(settings_obj.show_quarterly_notes)
        self.assertTrue(settings_obj.show_annual_notes)
        self.assertTrue(settings_obj.show_special_reports)
        self.assertTrue(settings_obj.show_research_by_asset_class)

    def test_super_admin_can_view_and_save(self):
        self.client.force_login(self.super_admin)
        url = reverse('home_page_settings')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Home Page Settings')
        self.assertContains(response, 'Featured Research')
        self.assertContains(response, 'Daily Note')
        self.assertContains(response, 'Weekly Insight')
        self.assertContains(response, 'Monthly Digest')
        self.assertContains(response, 'Quarterly Review')
        self.assertContains(response, 'Annual Outlook')
        self.assertContains(response, 'Special Report')
        self.assertContains(response, 'Research by Asset Class')
        self.assertNotContains(response, 'Weekly Notes')
        self.assertNotContains(response, 'Monthly Notes')

        response = self.client.post(url, {
            'show_featured_research': 'on',
            'show_latest_research': 'on',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        settings_obj = HomePageSettings.load()
        self.assertTrue(settings_obj.show_featured_research)
        self.assertTrue(settings_obj.show_latest_research)
        self.assertFalse(settings_obj.show_weekly_notes)
        self.assertFalse(settings_obj.show_special_reports)
        self.assertFalse(settings_obj.show_research_by_asset_class)

    def test_administrator_cannot_modify(self):
        self.client.force_login(self.administrator)
        response = self.client.get(reverse('home_page_settings'))
        self.assertEqual(response.status_code, 302)

    def test_client_home_shows_daily_and_weekly_notes(self):
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('client_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Daily Note<')
        self.assertContains(response, '>Weekly Insight<')
        self.assertContains(response, '>Monthly Digest<')
        self.assertContains(response, '>Quarterly Review<')
        self.assertContains(response, '>Annual Outlook<')
        self.assertContains(response, '>Special Report<')
        self.assertContains(response, 'All')
        self.assertNotContains(response, '>Latest Research<')
        self.assertNotContains(response, '>Weekly Notes<')
        self.assertNotContains(response, '>Monthly Notes<')

    def test_client_home_hides_disabled_sections(self):
        settings_obj = HomePageSettings.load()
        settings_obj.show_featured_research = False
        settings_obj.show_latest_research = False
        settings_obj.show_weekly_notes = False
        settings_obj.show_monthly_notes = False
        settings_obj.show_quarterly_notes = False
        settings_obj.show_annual_notes = False
        settings_obj.show_special_reports = False
        settings_obj.save()

        self.client.force_login(self.client_user)
        response = self.client.get(reverse('client_home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Featured Research<')
        self.assertNotContains(response, '>Daily Note<')
        self.assertNotContains(response, '>Latest Research<')
        self.assertNotContains(response, '>Weekly Insight<')
        self.assertNotContains(response, '>Monthly Digest<')
        self.assertNotContains(response, '>Quarterly Review<')
        self.assertNotContains(response, '>Annual Outlook<')
        self.assertNotContains(response, '>Special Report<')
        self.assertNotContains(response, '>Regular Publications<')

    def test_super_admin_can_preview_client_home(self):
        self.client.force_login(self.super_admin)
        url = reverse('client_home_preview')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Client Home preview')
        self.assertContains(response, '>Featured Research<')
        self.assertContains(response, '>Daily Note<')
        self.assertContains(response, '>Weekly Insight<')
        self.assertContains(response, '>Special Report<')
        self.assertContains(response, 'Live preview of the client portal Home page')
        self.assertContains(response, reverse('home_page_settings'))

    def test_preview_respects_home_page_settings(self):
        settings_obj = HomePageSettings.load()
        settings_obj.show_featured_research = False
        settings_obj.show_latest_research = False
        settings_obj.show_weekly_notes = False
        settings_obj.show_monthly_notes = False
        settings_obj.show_quarterly_notes = False
        settings_obj.show_annual_notes = False
        settings_obj.show_special_reports = False
        settings_obj.save()

        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('client_home_preview'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Featured Research<')
        self.assertNotContains(response, '>Daily Note<')
        self.assertNotContains(response, '>Weekly Insight<')
        self.assertNotContains(response, '>Monthly Digest<')
        self.assertNotContains(response, '>Special Report<')

    def test_preview_ajax_stays_on_preview_url(self):
        from modules.taxonomy.models import AssetClass
        AssetClass.objects.create(name='Equities')

        self.client.force_login(self.super_admin)
        response = self.client.get(
            reverse('client_home_preview'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'home-notes-tab')
        self.assertContains(response, reverse('client_home_preview'))
        self.assertNotContains(response, reverse('client_home'))
        self.assertNotContains(response, 'Client Home preview')

    def test_administrator_cannot_preview(self):
        self.client.force_login(self.administrator)
        response = self.client.get(reverse('client_home_preview'))
        self.assertEqual(response.status_code, 302)

    def test_settings_page_links_to_preview(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('home_page_settings'))
        self.assertContains(response, 'Preview client Home')
        self.assertContains(response, reverse('client_home_preview'))
