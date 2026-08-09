from __future__ import annotations
import os,shutil,sys
from playwright.sync_api import expect,sync_playwright
from browser_journeys import ADMIN,CSS,BACKEND_STUB,ADMIN_JS,INDEX,APP,install_storage,chromium_path

def load_admin(page,role='OWNER',mode='personal'):
    page.set_content(ADMIN);install_storage(page,'localStorage',{});install_storage(page,'sessionStorage',{});page.add_style_tag(content=CSS);page.add_script_tag(content=BACKEND_STUB);page.evaluate(f"window.__backend.authMode={mode!r};window.__backend.authRole={role!r}");page.add_script_tag(content=ADMIN_JS)

def main():
    exe=chromium_path()
    if not exe: raise SystemExit('No Chromium/Chrome executable found; set PA_TEST_CHROMIUM')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path=exe,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':1280,'height':900})
        admin=context.new_page();load_admin(admin);admin.locator('#admin').wait_for(state='visible');expect(admin.locator('#login')).to_be_hidden()
        for name in ('Дашборд','Провайдеры','Модели','Маршрутизация','Пользователи','Подписки и Usage','Сайты и поиск','VPS / Deploy','Мониторинг','Логи и аудит','Обратная связь','Диагностика','Система'): assert admin.get_by_role('button',name=name,exact=True).is_visible(),name
        admin.get_by_role('button',name='Провайдеры',exact=True).click();admin.locator('#providerType').select_option('openai_compatible');admin.locator('#providerName').fill('LM Studio');admin.locator('#providerUrl').fill('http://host.docker.internal:1234/v1');admin.locator('#providerKey').fill('secret-not-rendered');admin.locator('#providerBillingClass').select_option('PLATFORM_REMOTE');admin.locator('#addProvider').click();expect(admin.locator('#providerState')).to_contain_text('Подключено')
        admin.get_by_role('button',name='Модели',exact=True).click();assert 'external-model' in admin.locator('#models').inner_text();assert admin.locator('#models img').count()==0
        admin.get_by_role('button',name='Маршрутизация',exact=True).click();admin.locator('select[data-mode="smart"]').select_option('provider-test\u0000external-model');admin.locator('#saveRoutes').click();expect(admin.locator('#saveState')).to_contain_text('Сохранено')
        admin.get_by_role('button',name='Подписки и Usage',exact=True).click();expect(admin.locator('#billingPlans .billing-plan-row')).to_have_count(3);expect(admin.locator('#billingSetupChecklist')).to_be_visible();assert admin.locator('#billingSecret').get_attribute('type')=='password'
        admin.get_by_role('button',name='Сайты и поиск',exact=True).click();expect(admin.locator('#siteProfiles .provider-card')).to_have_count(2);expect(admin.locator('#searchProviderStatus')).to_contain_text('SearXNG')
        admin.get_by_role('button',name='Логи и аудит',exact=True).click();admin.locator('#refreshLogs').click();expect(admin.locator('#adminLogs')).to_contain_text('chat.completed');assert 'secret' not in admin.locator('#adminLogs').inner_text().lower()
        admin.get_by_role('button',name='Диагностика',exact=True).click();admin.locator('#refreshDiagnostics').click();expect(admin.locator('#adminDiagnostics')).to_contain_text('0.8.0-alpha.8')
        admin.close()
        user=context.new_page();user.set_content(INDEX);install_storage(user,'localStorage',{});install_storage(user,'sessionStorage',{});user.add_style_tag(content=CSS);user.add_script_tag(content=BACKEND_STUB);user.evaluate("window.__backend.authMode='accounts';window.__backend.authRole='USER'");user.add_script_tag(content=APP);expect(user.locator('#adminEntry')).to_be_hidden();user.close()
        owner=context.new_page();load_admin(owner,role='OWNER',mode='accounts');expect(owner.locator('#admin')).to_be_visible();expect(owner.locator('#login')).to_be_hidden();owner.close()
        context.close();browser.close()
    print('PAR_V080_ADMIN_BROWSER_ACCEPTANCE PASS: admin providers models routing billing search logs diagnostics role-boundary',flush=True)
    return 0
if __name__=='__main__': raise SystemExit(main())
