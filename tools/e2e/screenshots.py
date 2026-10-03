"""Screenshots of every screen at phone, tablet and laptop sizes, light and dark.

Run:  <venv>/bin/python tools/e2e/screenshots.py [output-dir]
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

from common import NEXT_PAGE, launch, static_server
import test_next_app as t

VIEWPORTS = {
    'phone': ({'width': 390, 'height': 844}, True),
    'phone-se': ({'width': 375, 'height': 667}, True),
    'phone-land': ({'width': 844, 'height': 390}, True),
    'ipad': ({'width': 820, 'height': 1180}, True),
    'ipad-land': ({'width': 1180, 'height': 820}, True),
    'laptop': ({'width': 1440, 'height': 900}, False),
}


async def capture(pw, base, out, name, viewport, mobile, theme):
    scripts = [f"try {{ localStorage.setItem('v2s_theme', '{theme}'); }} catch (e) {{}}"]
    browser, context, page, errors = await launch(pw, audio='fan', viewport=viewport, has_touch=mobile,
                                                  is_mobile=mobile, init_scripts=scripts)
    prefix = os.path.join(out, f'{name}-{theme}')

    async def shot(label):
        await page.wait_for_timeout(350)
        await page.screenshot(path=f'{prefix}-{label}.png')

    await page.goto(f'{base}/{NEXT_PAGE}')
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await shot('01-setup')
    await page.fill('#setupId', 'P017')
    await page.click('#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await page.click('#setupConfirmYes')
    try:
        await page.locator('#setupStepFolder:not([hidden])').wait_for(timeout=1500)
        await page.click('#setupFolderZip')
    except Exception:
        pass
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    await shot('02-welcome')
    await page.click('#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await t.wait_for(page, "() => document.getElementById('checkOk').getAttribute('aria-disabled') === 'false'")
    await shot('03-check')
    await page.click('#checkOk')
    await page.wait_for_selector('#screen-record:not([hidden])')
    await t.wait_for(page, "() => V2S.session.getState() === 'ready'")
    await shot('04-ready')
    await page.keyboard.press('Space')
    await page.wait_for_timeout(1200)
    await shot('05-recording')
    await page.keyboard.press('Space')
    await t.wait_ready(page)
    await shot('06-retry')
    await t.record(page, 1200, stop=False)
    await page.keyboard.press('Space')
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await shot('07-keep-dialog')
    await page.keyboard.press('Enter')
    await t.wait_ready(page)
    await page.evaluate("""async () => {
      const app = V2S.app.state();
      app.progress.currentIndex = 5 + 36;
      await V2S.storage.saveParticipantProgress(app.progress);
      await V2S.app.restartSession();
    }""")
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    await shot('08-welcome-back')
    await t.start_session(page)
    await shot('09-ready-formal')
    await page.evaluate("() => document.getElementById('finishButton').click()")
    await page.wait_for_selector('#screen-done:not([hidden])')
    await shot('10-done')
    print(name, theme, 'errors:', errors)
    await browser.close()

    # Second pass with speech so a take is accepted at the end of a block.
    browser, context, page, errors = await launch(pw, audio='speech', viewport=viewport, has_touch=mobile,
                                                  is_mobile=mobile, init_scripts=scripts)
    await t.setup_participant(page, base)
    await t.start_session(page)
    await t.set_index(page, 5 + 49)
    await shot('11-last-in-block')
    await t.record(page)
    await page.wait_for_selector('#screen-break:not([hidden])')
    await shot('12-break')
    async with page.expect_download():
        await page.click('#breakPrimary')
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await shot('13-save-confirm')
    await page.get_by_role('button', name='Yes, it saved').click()
    await page.wait_for_timeout(500)
    await shot('14-saved')
    print(name, theme, 'errors (pass 2):', errors)
    await browser.close()


async def main(out):
    os.makedirs(out, exist_ok=True)
    with static_server() as base:
        async with async_playwright() as pw:
            for name, (viewport, mobile) in VIEWPORTS.items():
                for theme in ('light', 'dark'):
                    await capture(pw, base, out, name, viewport, mobile, theme)


if __name__ == '__main__':
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), 'shots')))
