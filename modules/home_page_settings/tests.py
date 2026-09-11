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
        self.assertTrue(settings_obj.show_research_by_asset_class)
        self.assertEqual(settings_obj.top_notes_latest_research, 6)
        self.assertEqual(settings_obj.top_notes_weekly_notes, 6)
        self.assertEqual(settings_obj.top_notes_monthly_notes, 6)
        self.assertEqual(settings_obj.top_notes_quarterly_notes, 6)
        self.assertEqual(settings_obj.top_notes_annual_notes, 6)
        self.assertFalse(hasattr(settings_obj, 'cards_per_row_latest_research'))

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
        self.assertContains(response, 'Research by Asset Class')
        self.assertNotContains(response, 'Special Report')
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
        self.assertFalse(settings_obj.show_research_by_asset_class)

    def test_administrator_cannot_modify(self):
        self.client.force_login(self.administrator)
        response = self.client.get(reverse('home_page_settings'))
        self.assertEqual(response.status_code, 302)

    def test_client_home_shows_daily_and_weekly_notes(self):
        from modules.taxonomy.models import AssetClass
        AssetClass.objects.create(name='Equities')

        self.client.force_login(self.client_user)
        response = self.client.get(reverse('client_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Daily Note<')
        self.assertContains(response, '>Weekly Insight<')
        self.assertContains(response, '>Monthly Digest<')
        self.assertContains(response, '>Quarterly Review<')
        self.assertContains(response, '>Annual Outlook<')
        self.assertContains(response, 'All')
        self.assertContains(response, 'monthly_asset_class')
        self.assertContains(response, 'quarterly_asset_class')
        self.assertContains(response, 'annual_asset_class')
        self.assertNotContains(response, '>Latest Research<')
        self.assertNotContains(response, '>Weekly Notes<')
        self.assertNotContains(response, '>Monthly Notes<')
        self.assertNotContains(response, '>Special Report<')

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
        self.assertContains(response, '>Monthly Digest<')
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

    def test_settings_page_has_no_save_or_preview_buttons(self):
        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('home_page_settings'))
        self.assertNotContains(response, 'Preview client Home')
        self.assertNotContains(response, 'Save settings')
        self.assertContains(response, 'Click Edit to change')

    def test_ajax_toggle_saves_one_field(self):
        self.client.force_login(self.super_admin)
        url = reverse('home_page_settings')
        response = self.client.post(
            url,
            {'field': 'show_weekly_notes', 'value': 'off'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True})
        settings_obj = HomePageSettings.load()
        self.assertFalse(settings_obj.show_weekly_notes)
        self.assertTrue(settings_obj.show_featured_research)
        self.assertTrue(settings_obj.show_latest_research)

    def test_ajax_saves_section_display_name(self):
        self.client.force_login(self.super_admin)
        url = reverse('home_page_settings')
        response = self.client.post(
            url,
            {'field': 'title_weekly_notes', 'value': 'Weekly Notes'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'ok': True, 'label': 'Weekly Notes'})
        settings_obj = HomePageSettings.load()
        self.assertEqual(settings_obj.title_weekly_notes, 'Weekly Notes')
        self.assertEqual(settings_obj.heading_for_toggle('show_weekly_notes'), 'Weekly Notes')
        self.assertTrue(settings_obj.show_weekly_notes)

        response = self.client.get(url)
        self.assertContains(response, 'Weekly Notes')
        self.assertContains(response, 'data-edit-section')
        self.assertContains(response, 'section-edit-save')

    def test_pencil_opens_section_modal(self):
        try:
            from playwright.sync_api import expect, sync_playwright
        except ImportError:
            self.skipTest('playwright is not installed')

        self.client.force_login(self.super_admin)
        html = self.client.get(reverse('home_page_settings')).content.decode()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until='domcontentloaded')

            weekly = page.locator('[data-section-row]', has_text='Weekly Insight')
            modal = page.locator('#section-edit-modal')
            expect(modal).to_be_hidden()
            weekly.locator('[data-edit-section]').click()

            expect(modal).to_be_visible()
            expect(page.locator('#section-edit-name')).to_have_value('Weekly Insight')
            expect(page.locator('#section-edit-top-notes')).to_have_value('6')
            expect(page.locator('#section-edit-enabled')).to_be_checked()
            expect(page.locator('#section-edit-save')).to_be_visible()
            expect(page.locator('#section-edit-cancel')).to_be_visible()

            page.locator('#section-edit-cancel').click()
            expect(modal).to_be_hidden()

            browser.close()

    def test_blank_display_name_restores_default(self):
        settings_obj = HomePageSettings.load()
        settings_obj.title_weekly_notes = 'Weekly Notes'
        settings_obj.save()

        self.client.force_login(self.super_admin)
        response = self.client.post(
            reverse('home_page_settings'),
            {'field': 'title_weekly_notes', 'value': '  '},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.json(), {'ok': True, 'label': 'Weekly Insight'})
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.title_weekly_notes, '')
        self.assertEqual(settings_obj.heading_for_toggle('show_weekly_notes'), 'Weekly Insight')

    def test_client_home_uses_custom_section_names(self):
        from modules.taxonomy.models import AssetClass
        AssetClass.objects.create(name='Equities')

        settings_obj = HomePageSettings.load()
        settings_obj.title_featured_research = 'Spotlight'
        settings_obj.title_latest_research = 'Morning Brief'
        settings_obj.title_weekly_notes = 'Weekly Notes'
        settings_obj.title_research_by_asset_class = 'By Asset Class'
        settings_obj.save()

        self.client.force_login(self.client_user)
        response = self.client.get(reverse('client_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Spotlight<')
        self.assertContains(response, '>Morning Brief<')
        self.assertContains(response, '>Weekly Notes<')
        self.assertContains(response, '>By Asset Class<')
        self.assertNotContains(response, '>Featured Research<')
        self.assertNotContains(response, '>Daily Note<')
        self.assertNotContains(response, '>Weekly Insight<')
        self.assertNotContains(response, '>Research by Asset Class<')

    def test_preview_uses_custom_section_names(self):
        settings_obj = HomePageSettings.load()
        settings_obj.title_weekly_notes = 'Weekly Notes'
        settings_obj.save()

        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('client_home_preview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '>Weekly Notes<')
        self.assertNotContains(response, '>Weekly Insight<')

    def test_client_cannot_edit_section_names(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse('home_page_settings'),
            {'field': 'title_weekly_notes', 'value': 'Weekly Notes'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 302)
        settings_obj = HomePageSettings.load()
        self.assertEqual(settings_obj.title_weekly_notes, '')

    def test_ajax_saves_top_notes_per_section(self):
        self.client.force_login(self.super_admin)
        url = reverse('home_page_settings')
        response = self.client.get(url)
        self.assertContains(response, 'Cards')
        self.assertContains(response, '6 cards')
        self.assertContains(response, 'data-top-notes-field="top_notes_latest_research"')
        self.assertContains(response, 'data-top-notes-field="top_notes_weekly_notes"')
        self.assertContains(response, 'data-top-notes-field="top_notes_monthly_notes"')
        self.assertContains(response, 'data-top-notes-field="top_notes_quarterly_notes"')
        self.assertContains(response, 'data-top-notes-field="top_notes_annual_notes"')
        self.assertNotContains(response, 'Cards per row')
        self.assertNotContains(response, 'data-cards-field')
        self.assertNotContains(response, 'cards_per_row')
        self.assertNotContains(response, 'Top notes')
        self.assertNotContains(response, '>Top 6<')
        self.assertContains(response, 'id="section-edit-top-notes"')
        self.assertContains(response, 'type="number"')
        self.assertNotContains(response, '<option value="6">')
        html = response.content.decode()
        self.assertRegex(html, r'data-field="show_featured_research"[\s\S]{0,400}?data-uses-top-notes="0"')
        self.assertRegex(html, r'data-field="show_research_by_asset_class"[\s\S]{0,400}?data-uses-top-notes="0"')
        self.assertRegex(html, r'data-field="show_latest_research"[\s\S]{0,400}?data-uses-top-notes="1"')

        response = self.client.post(
            url,
            {
                'action': 'save_section',
                'field': 'show_weekly_notes',
                'title': 'Weekly Insight',
                'top_notes': '8',
                'enabled': 'on',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'ok': True,
            'label': 'Weekly Insight',
            'top_notes': 8,
            'on': True,
        })
        settings_obj = HomePageSettings.load()
        self.assertEqual(settings_obj.top_notes_weekly_notes, 8)
        self.assertEqual(settings_obj.top_notes_latest_research, 6)
        self.assertEqual(settings_obj.top_notes_monthly_notes, 6)
        self.assertEqual(settings_obj.top_notes_quarterly_notes, 6)
        self.assertEqual(settings_obj.top_notes_annual_notes, 6)
        self.assertTrue(settings_obj.show_weekly_notes)

        response = self.client.post(
            url,
            {'field': 'top_notes_monthly_notes', 'value': '11'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.json(), {'ok': True, 'top_notes': 11})
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.top_notes_weekly_notes, 8)
        self.assertEqual(settings_obj.top_notes_monthly_notes, 11)

        html = self.client.get(url).content.decode()
        self.assertIn('data-top-notes-field="top_notes_weekly_notes"', html)
        self.assertRegex(html, r'data-top-notes-field="top_notes_weekly_notes"[\s\S]{0,250}?data-top-notes="8"')
        self.assertRegex(html, r'data-top-notes-field="top_notes_monthly_notes"[\s\S]{0,250}?data-top-notes="11"')

    def test_ajax_saves_section_name_top_notes_and_status(self):
        self.client.force_login(self.super_admin)
        response = self.client.post(
            reverse('home_page_settings'),
            {
                'action': 'save_section',
                'field': 'show_monthly_notes',
                'title': 'Month Ahead',
                'top_notes': '10',
                'enabled': 'off',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.json(), {
            'ok': True,
            'label': 'Month Ahead',
            'top_notes': 10,
            'on': False,
        })
        settings_obj = HomePageSettings.load()
        self.assertEqual(settings_obj.title_monthly_notes, 'Month Ahead')
        self.assertEqual(settings_obj.top_notes_monthly_notes, 10)
        self.assertFalse(settings_obj.show_monthly_notes)
        self.assertTrue(settings_obj.show_weekly_notes)
        self.assertEqual(settings_obj.top_notes_weekly_notes, 6)
        self.assertEqual(settings_obj.title_weekly_notes, '')

    def test_invalid_top_notes_falls_back_to_six(self):
        settings_obj = HomePageSettings.load()
        settings_obj.top_notes_weekly_notes = 10
        settings_obj.save()

        self.client.force_login(self.super_admin)
        response = self.client.post(
            reverse('home_page_settings'),
            {'field': 'top_notes_weekly_notes', 'value': '0'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.json(), {'ok': True, 'top_notes': 6})
        settings_obj.refresh_from_db()
        self.assertEqual(settings_obj.top_notes_weekly_notes, 6)
        self.assertEqual(settings_obj.top_notes_latest_research, 6)

    def test_client_home_and_preview_use_section_top_notes(self):
        from datetime import timedelta

        from django.utils import timezone
        from modules.taxonomy.models import AssetClass, PublicationType

        AssetClass.objects.create(name='Equities', show_on_home=True)
        weekly_type, _ = PublicationType.objects.get_or_create(
            slug='weekly-insight',
            defaults={'name': 'Weekly Insight'},
        )
        now = timezone.now()
        for i in range(12):
            self._published_daily_note(
                title=f'Daily note {i:02d}',
                published_at=now - timedelta(hours=12 - i),
            )
        for i in range(8):
            self._published_daily_note(
                title=f'Weekly note {i:02d}',
                published_at=now - timedelta(hours=8 - i),
                publication_type=weekly_type,
            )

        settings_obj = HomePageSettings.load()
        settings_obj.top_notes_latest_research = 10
        settings_obj.top_notes_weekly_notes = 6
        settings_obj.save()

        self.client.force_login(self.client_user)
        response = self.client.get(reverse('client_home'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('id="daily-note-container"', html)
        self.assertIn('id="weekly-notes-container"', html)
        self.assertNotIn('--home-cards-per-row', html)
        self.assertIn('home-cards-grid', html)
        self.assertIn('home-asset-class-grid', html)
        self.assertIn('Daily note 11', html)
        self.assertIn('Daily note 02', html)
        self.assertNotIn('Daily note 01', html)
        self.assertNotIn('Daily note 00', html)
        self.assertIn('Weekly note 07', html)
        self.assertIn('Weekly note 02', html)
        self.assertNotIn('Weekly note 01', html)
        self.assertNotIn('Weekly note 00', html)

        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('client_home_preview'))
        self.assertEqual(response.status_code, 200)
        preview = response.content.decode()
        self.assertIn('Daily note 11', preview)
        self.assertNotIn('Daily note 01', preview)
        self.assertIn('Weekly note 07', preview)
        self.assertNotIn('Weekly note 01', preview)
        self.assertNotIn('--home-cards-per-row', preview)

    def test_client_cannot_change_top_notes(self):
        self.client.force_login(self.client_user)
        response = self.client.post(
            reverse('home_page_settings'),
            {'field': 'top_notes_weekly_notes', 'value': '10'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 302)
        settings_obj = HomePageSettings.load()
        self.assertEqual(settings_obj.top_notes_weekly_notes, 6)

    def _published_daily_note(self, **kwargs):
        from django.utils import timezone
        from modules.reports.models import Report
        from modules.taxonomy.models import PublicationType

        publication_type, _ = PublicationType.objects.get_or_create(
            slug='daily-note',
            defaults={'name': 'Daily Note'},
        )
        defaults = {
            'title': 'Morning rates note',
            'status': Report.STATUS_PUBLISHED,
            'published_at': timezone.now(),
            'content_type': Report.CONTENT_TEXT,
            'body': '<p>Overnight moves in rates.</p>',
            'publication_type': publication_type,
            'author': self.super_admin,
        }
        defaults.update(kwargs)
        return Report.objects.create(**defaults)

    def test_preview_cards_open_client_reader_not_content(self):
        report = self._published_daily_note()
        featured = self._published_daily_note(
            title='Featured rates outlook',
            is_featured=True,
            body='<p>Featured body</p>',
        )
        preview_url = reverse('client_home_preview_report', args=[report.id])
        featured_url = reverse('client_home_preview_report', args=[featured.id])

        self.client.force_login(self.super_admin)
        response = self.client.get(reverse('client_home_preview'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn(preview_url, html)
        self.assertIn(featured_url, html)
        self.assertNotIn(reverse('report_edit', args=[report.id]), html)
        self.assertNotIn(reverse('report_edit', args=[featured.id]), html)
        self.assertNotContains(response, 'Open in Content')

        ajax = self.client.get(
            reverse('client_home_preview'),
            {'home_section': 'daily'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(ajax.status_code, 200)
        ajax_html = ajax.content.decode()
        self.assertIn(preview_url, ajax_html)
        self.assertNotIn(reverse('report_edit', args=[report.id]), ajax_html)

        reader = self.client.get(preview_url)
        self.assertEqual(reader.status_code, 200)
        self.assertContains(reader, 'Morning rates note')
        self.assertContains(reader, 'Overnight moves in rates.')
        self.assertContains(reader, 'Back to preview')
        self.assertContains(reader, reverse('client_home_preview'))
        self.assertNotContains(reader, 'name="title"')
        self.assertContains(reader, 'Client Home preview')

    def test_administrator_cannot_open_preview_reader(self):
        report = self._published_daily_note()
        url = reverse('client_home_preview_report', args=[report.id])

        self.client.force_login(self.administrator)
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.client_user)
        self.assertEqual(self.client.get(url).status_code, 302)

    def test_client_home_still_opens_portal_reader(self):
        report = self._published_daily_note()
        self.client.force_login(self.client_user)
        response = self.client.get(reverse('client_home'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn(reverse('client_report_detail', args=[report.id]), html)
        self.assertNotIn(reverse('client_home_preview_report', args=[report.id]), html)
        self.assertNotIn(reverse('report_edit', args=[report.id]), html)
