from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from modules.roles.models import Role


class ReportFormEditorTests(TestCase):
    def setUp(self):
        User = get_user_model()
        role = Role.objects.get(slug='super-admin')
        self.user = User.objects.create_user('editor', 'editor@example.com', 'pass')
        self.user.profile.role = role
        self.user.profile.save()

    def test_create_content_page_has_deletable_block_controls(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_add'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="block-editor"', content)
        self.assertIn('block-gutter', content)
        self.assertIn('data-block-action', content)
        self.assertIn('Delete block', content)
        self.assertIn('runBlockAction', content)
        self.assertIn("action === 'delete'", content)

    def test_delete_button_removes_middle_block(self):
        try:
            from playwright.sync_api import expect, sync_playwright
        except ImportError:
            self.skipTest('playwright is not installed')

        self.client.force_login(self.user)
        html = self.client.get(reverse('report_add')).content.decode()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until='domcontentloaded')
            page.wait_for_selector('#block-editor .block-text')

            def add_section(index, text):
                target = page.locator('.block-text').nth(index)
                target.click()
                expect(target).to_be_focused()
                target.type(text)

            add_section(0, 'alpha')
            page.locator('.insert-gap').nth(0).hover()
            page.locator('.insert-plus').nth(0).click()
            page.locator('.insert-gap.is-open .insert-picker button', has_text='Text').click()
            expect(page.locator('.editor-block')).to_have_count(2)
            add_section(1, 'bravo')
            page.locator('.insert-gap').nth(1).hover()
            page.locator('.insert-plus').nth(1).click()
            page.locator('.insert-gap.is-open .insert-picker button', has_text='Text').click()
            expect(page.locator('.editor-block')).to_have_count(3)
            add_section(2, 'charlie')

            texts = page.locator('.block-text').all_inner_texts()
            self.assertEqual([t.strip() for t in texts], ['alpha', 'bravo', 'charlie'])

            middle = page.locator('.editor-block').nth(1)
            middle.hover()
            middle.locator('[data-block-action="delete"]').click()

            expect(page.locator('.editor-block')).to_have_count(2)
            remaining = [t.strip() for t in page.locator('.block-text').all_inner_texts()]
            self.assertEqual(remaining, ['alpha', 'charlie'])

            page.locator('.editor-block').nth(0).hover()
            page.locator('.editor-block').nth(0).locator('[data-block-action="delete"]').click()
            expect(page.locator('.editor-block')).to_have_count(1)
            self.assertEqual(page.locator('.block-text').inner_text().strip(), 'charlie')

            browser.close()

    def test_plus_adds_aligned_next_line_that_can_be_deleted(self):
        try:
            from playwright.sync_api import expect, sync_playwright
        except ImportError:
            self.skipTest('playwright is not installed')

        self.client.force_login(self.user)
        html = self.client.get(reverse('report_add')).content.decode()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until='domcontentloaded')
            page.wait_for_selector('#block-editor .block-text')

            first = page.locator('.block-text').nth(0)
            first.click()
            first.type('alpha')

            page.locator('.insert-gap').nth(0).hover()
            page.locator('.insert-plus').nth(0).click()
            page.locator('.insert-gap.is-open .insert-picker button', has_text='Text').click()

            expect(page.locator('.editor-block')).to_have_count(2)
            second = page.locator('.block-text').nth(1)
            expect(second).to_be_focused()
            second.type('bravo')

            texts = [t.strip() for t in page.locator('.block-text').all_inner_texts()]
            self.assertEqual(texts, ['alpha', 'bravo'])

            first_box = page.locator('.block-text').nth(0).bounding_box()
            second_box = page.locator('.block-text').nth(1).bounding_box()
            self.assertIsNotNone(first_box)
            self.assertIsNotNone(second_box)
            self.assertLess(first_box['y'], second_box['y'])
            self.assertAlmostEqual(first_box['x'], second_box['x'], delta=2)

            page.locator('.editor-block').nth(1).hover()
            page.locator('.editor-block').nth(1).locator('[data-block-action="delete"]').click()
            expect(page.locator('.editor-block')).to_have_count(1)
            self.assertEqual(page.locator('.block-text').inner_text().strip(), 'alpha')

            browser.close()

    def test_enter_stays_inside_the_same_section(self):
        try:
            from playwright.sync_api import expect, sync_playwright
        except ImportError:
            self.skipTest('playwright is not installed')

        self.client.force_login(self.user)
        html = self.client.get(reverse('report_add')).content.decode()

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until='domcontentloaded')
            page.wait_for_selector('#block-editor .block-text')

            first = page.locator('.block-text').nth(0)
            first.click()
            first.type('alpha')
            page.keyboard.press('Enter')
            first.type('bravo')

            expect(page.locator('.editor-block')).to_have_count(1)
            text = page.locator('.block-text').inner_text()
            self.assertIn('alpha', text)
            self.assertIn('bravo', text)

            browser.close()

    def test_create_content_page_has_article_pdf_attach(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('report_add'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('id="article-attach-section"', content)
        self.assertIn('id="article-attach-preview-btn"', content)
        self.assertIn('Attach File', content)
        self.assertIn('gcio-pdf-chip', content)
        self.assertIn('canvas-title-input', content)
        self.assertIn('id="id_title"', content)
        self.assertRegex(content, r'<textarea[^>]*id="id_title"')

    def test_text_article_can_attach_pdf_without_changing_type(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.utils import timezone
        from modules.reports.models import Report

        pdf = SimpleUploadedFile(
            'briefing.pdf',
            b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<>\n%%EOF\n',
            content_type='application/pdf',
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse('report_add'), {
            'content_type': Report.CONTENT_TEXT,
            'title': 'Rates note with PDF',
            'description': 'Summary',
            'body': '<p>Overnight moves.</p>',
            'status': Report.STATUS_PUBLISHED,
            'access_level': Report.ACCESS_ALL,
            'page_count': 5,
            'published_at': timezone.now().date().isoformat(),
            'article_attachment': pdf,
        })
        self.assertEqual(response.status_code, 302)
        report = Report.objects.get(title='Rates note with PDF')
        self.assertEqual(report.content_type, Report.CONTENT_TEXT)
        self.assertTrue(report.article_attachment.name.lower().endswith('.pdf'))
        self.assertFalse(bool(report.file_upload))
        self.assertEqual(report.page_count, 5)

        edit = self.client.get(reverse('report_edit', args=[report.id]))
        self.assertEqual(edit.status_code, 200)
        html = edit.content.decode()
        self.assertIn(report.article_attachment.url, html)
        self.assertIn('const existingFileUrl = "" || null;', html)

    def test_text_article_rejects_non_pdf_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from modules.reports.models import Report

        pptx = SimpleUploadedFile(
            'deck.pptx',
            b'not-a-pdf',
            content_type='application/vnd.openxmlformats-officedocument.presentationml.presentation',
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse('report_add'), {
            'content_type': Report.CONTENT_TEXT,
            'title': 'Should not save',
            'body': '<p>Body</p>',
            'status': Report.STATUS_DRAFT,
            'access_level': Report.ACCESS_ALL,
            'page_count': 1,
            'article_attachment': pptx,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'must be a PDF')
        self.assertFalse(Report.objects.filter(title='Should not save').exists())

    def test_client_article_shows_attached_pdf_preview(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.utils import timezone
        from modules.reports.models import Report
        from modules.roles.models import Role

        User = get_user_model()
        client_role = Role.objects.get(slug='client-user')
        client_user = User.objects.create_user('reader', 'reader@example.com', 'pass')
        client_user.profile.role = client_role
        client_user.profile.save()

        pdf = SimpleUploadedFile(
            'briefing.pdf',
            b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<>\n%%EOF\n',
            content_type='application/pdf',
        )
        report = Report.objects.create(
            title='Client article with PDF',
            body='<p>Overnight moves in rates.</p>',
            content_type=Report.CONTENT_TEXT,
            status=Report.STATUS_PUBLISHED,
            published_at=timezone.now(),
            access_level=Report.ACCESS_ALL,
            article_attachment=pdf,
        )

        self.client.force_login(client_user)
        response = self.client.get(reverse('client_report_detail', args=[report.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Overnight moves in rates.')
        self.assertContains(response, 'id="view-pdf-btn"')
        self.assertContains(response, 'id="attached-pdf-card"')
        self.assertContains(response, 'gcio-pdf-chip')
        self.assertContains(response, 'One attachment')
        self.assertContains(response, 'id="pdf-viewer-modal"')
