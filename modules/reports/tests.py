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

            def add_line(index, text):
                target = page.locator('.block-text').nth(index)
                target.click()
                expect(target).to_be_focused()
                target.type(text)

            add_line(0, 'alpha')
            page.keyboard.press('Enter')
            expect(page.locator('.editor-block')).to_have_count(2)
            add_line(1, 'bravo')
            page.keyboard.press('Enter')
            expect(page.locator('.editor-block')).to_have_count(3)
            add_line(2, 'charlie')

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
            page.locator('.insert-picker button', has_text='Text').click()

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
