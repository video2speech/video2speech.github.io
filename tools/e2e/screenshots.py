"""Screenshots of every screen on phones, tablets and a laptop, in light and dark.

Run:  <venv>/bin/python tools/e2e/screenshots.py [--engine webkit] [OUT_DIR] [--only phone ipad]

Silent (common.launch mutes every browser). The synthetic voice speaks during takes.
"""
import asyncio
import os
import sys

from playwright.async_api import async_playwright

from common import NEXT_PAGE, launch, next_url, static_server
import test_next_app as t
from test_next_app import click

VIEWPORTS = {
    'phone': ({'width': 390, 'height': 844}, True),
    'phone-land': ({'width': 844, 'height': 390}, True),
    'ipad-mini': ({'width': 744, 'height': 1133}, True),
    'ipad': ({'width': 820, 'height': 1180}, True),
    'ipad-land': ({'width': 1180, 'height': 820}, True),
    'laptop': ({'width': 1440, 'height': 900}, False),
    # What an iPhone shows inside Safari's bars: an SE upright, an iPhone 15 sideways.
    'phone-safari': ({'width': 375, 'height': 553}, True),
    'phone-land-safari': ({'width': 750, 'height': 340}, True),
}

ENGINE = 'chrome'
EXTRA_INIT = []   # more scripts before the page loads (e.g. an upright camera)


async def capture(pw, base, out, name, viewport, mobile, theme):
    theme_js = f"try {{ localStorage.setItem('v2s_theme', '{theme}'); }} catch (e) {{}}"
    prefix = os.path.join(out, f'{name}-{theme}')
    common = dict(viewport=viewport, has_touch=mobile, is_mobile=mobile, engine=ENGINE)

    # Sign-in page (not signed in yet).
    browser, _, page, errors = await launch(pw, authed=False, media='shim', init_scripts=[theme_js], **common)
    await page.goto(f'{base}/index.html')
    await page.wait_for_selector('#loginForm')
    await page.wait_for_timeout(400)
    await page.screenshot(path=f'{prefix}-00-signin.png')
    cut = await page.evaluate("() => { const r = document.querySelector('#loginForm button[type=submit]').getBoundingClientRect(); return r.bottom > window.innerHeight + 1; }")
    if cut:
        print(f'  OFFSCREEN {name}-{theme}-00-signin: Sign in')
    await browser.close()

    browser, _, page, errors = await launch(pw, audio='speech', media='shim', init_scripts=[theme_js, t.NO_PICKERS, t.FAST, *EXTRA_INIT], **common)

    # Anything wider than the screen (or the settings panel) is printed as a problem.
    overflow_js = """() => {
      const limit = window.innerWidth + 1;
      // Text cut off with an ellipsis inside a box that fits is not an overflow.
      const clippedInside = n => {
        for (let p = n.parentElement; p && p !== document.body; p = p.parentElement) {
          const o = getComputedStyle(p).overflowX;
          if ((o === 'hidden' || o === 'clip') && p.getBoundingClientRect().right <= limit) return true;
        }
        return false;
      };
      const wide = [...document.querySelectorAll('body *')].filter(n => {
        if (!n.getClientRects().length || n.closest('svg')) return false;  // SVG shapes are clipped by their frame
        const r = n.getBoundingClientRect();
        return r.width > 0 && r.right > limit && getComputedStyle(n).visibility !== 'hidden' && !clippedInside(n);
      });
      const sheet = document.querySelector('#settingsPanel:not([hidden]) .sheet');
      // Buttons whose content does not fit inside them (a label spilling over the edge).
      const spill = [...document.querySelectorAll('button')].filter(b => b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden' && b.scrollWidth > b.clientWidth + 1);
      return { page: document.documentElement.scrollWidth - window.innerWidth, sheet: sheet ? sheet.scrollWidth - sheet.clientWidth : 0,
               tall: document.documentElement.scrollHeight - window.innerHeight,
               // the screen's main button must be fully on screen, without scrolling
               offscreen: [...document.querySelectorAll('.btn-xl, .btn-main, #loginForm button[type=submit]')]
                 .filter(b => b.getClientRects().length && getComputedStyle(b).visibility !== 'hidden' && !b.closest('[hidden]'))
                 .filter(b => { const r = b.getBoundingClientRect(); return r.bottom > window.innerHeight + 1 || r.top < 0; })
                 .map(b => b.id || b.textContent.trim().slice(0, 20)),
               // words that do not fit their (scrolling) area: a line cut or faded at its edge
               clipped: [...document.querySelectorAll('.flow-body, .dialog-body, .check-panel')]
                 .filter(n => n.getClientRects().length && n.scrollHeight > n.clientHeight + 1)
                 .map(n => `${n.parentElement && n.parentElement.closest('[id]') ? n.parentElement.closest('[id]').id : ''}.${n.className}`),
               wide: wide.slice(0, 3).map(n => `${n.tagName}#${n.id}.${n.className}`),
               spill: spill.slice(0, 3).map(b => `${b.id || b.textContent.trim().slice(0, 20)}`) };
    }"""

    async def shot(label):
        await page.wait_for_timeout(350)
        await page.screenshot(path=f'{prefix}-{label}.png')
        r = await page.evaluate(overflow_js)
        if r['page'] > 1 or r['sheet'] > 1 or r['wide'] or r['spill']:
            print(f'  OVERFLOW {name}-{theme}-{label}: {r}')
        # Taller than the screen: the main button may need scrolling to be seen.
        if r['tall'] > 1:
            print(f'  VSCROLL {name}-{theme}-{label}: {r["tall"]} px')
        if r['clipped']:
            print(f'  CLIPPED {name}-{theme}-{label}: {r["clipped"]}')
        if r['offscreen']:
            print(f'  OFFSCREEN {name}-{theme}-{label}: {r["offscreen"]}')

    # Phones and tablets are driven by taps (their instructions name the buttons);
    # computers by the keyboard (their instructions name Space and ←).
    # Like a person: never within the page's double-press window.
    async def press_main():
        await t.ready_for_press(page)
        if mobile:
            await page.tap('#mainButton')
        else:
            await page.keyboard.press('Space')

    async def press_redo():
        await t.ready_for_press(page)
        if mobile:
            await page.tap('#redoButton')
        else:
            await page.keyboard.press('ArrowLeft')

    async def take(stop=True, ms=1500):
        await press_main()
        await page.wait_for_function("() => V2S.session.getState() === 'recording'", timeout=5000)
        await page.wait_for_timeout(ms)
        if stop:
            await finish_take()

    # Each take's outcome is printed, so a screenshot never silently shows the wrong state.
    async def finish_take():
        await press_main()
        await t.wait_ready(page)
        event = await page.evaluate("""async () => {
          await V2S.session.flush();
          let last = null;
          await V2S.storage.forEachTake(r => { last = r; });
          const q = (last && last.metadata && last.metadata.qc) || {};
          return { status: last && last.status, speechMs: q.speechMs, frames: q.frames, durationMs: q.durationMs, floor: q.noiseFloor, threshold: q.speechThreshold, interval: q.frameIntervalMs };
        }""")
        print(f"  {name}-{theme} take: {event}")

    await page.goto(next_url(base))
    await page.wait_for_selector('#screen-setup:not([hidden])', timeout=15000)
    await shot('01-setup')
    await page.fill('#setupId', 'semg1')
    await click(page, '#setupNext')
    await page.wait_for_selector('#setupStepConfirm:not([hidden])')
    await shot('02-setup-confirm')
    await click(page, '#setupConfirmYes')
    await page.wait_for_selector('#screen-welcome:not([hidden])', timeout=15000)
    await shot('03-welcome')
    await click(page, '#welcomeStart')
    await page.wait_for_selector('#screen-check:not([hidden])')
    await t.wait_for(page, "() => V2S.media.getStream() && document.getElementById('checkBadge').textContent === ''")
    await shot('04-check')
    await click(page, '#checkNext')
    await page.wait_for_selector('#checkStepMic:not([hidden])')
    await shot('04b-check-mic')
    await click(page, '#testRecord')
    await page.wait_for_timeout(600)
    await shot('05-check-recording')
    await t.wait_for(page, "() => !document.getElementById('testAsk').hidden", timeout=15000)
    await shot('06-check-ask')
    await click(page, '#testYes')
    await page.wait_for_selector('#screen-intro:not([hidden])')
    await shot('06b-intro')
    await click(page, '#introStart')
    await t.wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('08-practice-ready')
    await click(page, '#helpButton')
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await shot('07-help')
    await t.dialog_ready(page)
    await page.locator('#dialogActions button').first.click()
    await t.wait_for(page, "() => V2S.session.getState() === 'ready'")
    await page.wait_for_timeout(500)  # presses right after a dialog closes are ignored (double tap)
    await page.evaluate("window.__v2sAudio.set('speech')")
    await take(stop=False)
    await shot('09-practice-recording')
    await finish_take()
    await take()
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('10-practice-redo-lesson')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await press_redo()  # do the Redo lesson
    await page.wait_for_timeout(400)
    await take()
    for _ in range(3):
        await take()
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('11-practice-end')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await press_main()
    await page.wait_for_selector('#screen-break:not([hidden])')
    await t.wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    await shot('12-practice-done')
    # Saving is learnt here: the practice recordings are saved once (ZIP mode).
    async with page.expect_download():
        await click(page, '#breakPrimary')
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await t.dialog_ready(page)
    await page.get_by_role('button', name='Yes, I see it').click()
    await page.wait_for_timeout(500)
    await shot('12b-practice-saved')
    await click(page, '#breakPrimary')  # Continue to part 1
    await t.wait_ready(page)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('13-ready')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await take(stop=False)
    await shot('14-recording')
    await finish_take()
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('15-saved-redo')
    await t.ready_for_press(page)
    if mobile:
        box = await page.locator('#mainButton').bounding_box()
        await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
        await page.mouse.down()
    else:
        await page.keyboard.down('Space')
    await page.wait_for_timeout(1400)
    await shot('16-hold-dialog')
    if mobile:
        await page.mouse.up()
    else:
        await page.keyboard.up('Space')
    await t.dialog_ready(page)
    await page.locator('#dialogActions button').first.click()
    await t.wait_ready(page)
    await page.wait_for_timeout(200)
    await page.evaluate("window.__v2sAudio.set('fan')")
    await take()
    await shot('17-no-speech')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await press_redo()
    await page.wait_for_timeout(400)
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('18-redoing')
    await press_redo()  # Cancel redo
    await page.wait_for_timeout(400)
    await page.evaluate("window.__v2sAudio.set('speech')")
    await click(page, '#settingsButton')
    await page.wait_for_selector('#settingsPanel:not([hidden])')
    await shot('19-settings')
    await page.get_by_role('button', name='Saving').click()
    await page.wait_for_timeout(300)
    await shot('19b-settings-saving')
    await click(page, '#settingsBack')
    await page.get_by_role('button', name='Sentences & progress').click()
    await page.wait_for_timeout(300)
    await shot('19c-settings-progress')
    await click(page, '#settingsClose')
    await click(page, '#finishButton')
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await shot('20-end-dialog')
    await page.wait_for_timeout(450)  # dialogs ignore presses in their first 350 ms
    await page.get_by_role('button', name='Keep going').click()
    await page.wait_for_timeout(600)
    await t.set_index(page, 5 + 49)
    await take()
    await page.evaluate("window.__v2sAudio.set('silence')")
    await shot('21-part-end')
    await page.evaluate("window.__v2sAudio.set('speech')")
    await press_main()
    await page.wait_for_selector('#screen-break:not([hidden])')
    await t.wait_for(page, "() => !document.getElementById('breakPrimary').hidden")
    await shot('22-break')
    async with page.expect_download():
        await click(page, '#breakPrimary')
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await shot('23-save-confirm')
    await t.dialog_ready(page)
    await page.get_by_role('button', name='Yes, I see it').click()
    await page.wait_for_timeout(500)
    await shot('24-saved')
    await click(page, '#finishButton')   # End for today (top bar) asks first
    await t.wait_for(page, '() => V2S.ui.isDialogOpen()')
    await t.dialog_ready(page)
    await page.locator('#dialogActions button', has_text='End for today').click()
    await page.wait_for_selector('#screen-done:not([hidden])')
    await page.wait_for_timeout(600)
    await shot('25-done')
    await click(page, '#doneAgain')  # Record more → Welcome back
    await page.wait_for_selector('#screen-welcome:not([hidden])')
    await page.wait_for_timeout(300)
    await shot('26-welcome-back')
    print(name, theme, 'errors:', errors)
    await browser.close()


async def main(out, names, themes):
    os.makedirs(out, exist_ok=True)
    with static_server() as base:
        async with async_playwright() as pw:
            for name in names:
                viewport, mobile = VIEWPORTS[name]
                for theme in themes:
                    try:
                        await capture(pw, base, out, name, viewport, mobile, theme)
                    except Exception as error:
                        print(name, theme, 'FAILED:', repr(error))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--engine', choices=['chrome', 'webkit', 'firefox'], default='chrome')
    parser.add_argument('--only', nargs='*', help='viewport names, e.g. phone ipad')
    parser.add_argument('--theme', choices=['light', 'dark'], help='one theme only')
    parser.add_argument('out', nargs='?', default=os.path.join(os.path.dirname(__file__), 'shots'))
    args = parser.parse_args()
    ENGINE = args.engine
    t.ENGINE = args.engine
    asyncio.run(main(args.out, args.only or list(VIEWPORTS), [args.theme] if args.theme else ['light', 'dark']))
