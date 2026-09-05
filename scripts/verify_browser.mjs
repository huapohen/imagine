import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const runtime=process.env.IMAGINE_NODE_MODULES||'/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const req=createRequire(path.join(runtime,'_resolver.cjs'));
const {chromium}=req('playwright');
const output=path.join(root,'docs/verification/browser');
await fs.mkdir(output,{recursive:true});
const tokens=JSON.parse(await fs.readFile(path.join(root,'.local/browser-qa-tokens.json'),'utf8'));
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const ctx=await browser.newContext({viewport:{width:1440,height:960},recordVideo:{dir:path.join(root,'.local/qa-recording'),size:{width:1440,height:960}}});
const page=await ctx.newPage();
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const checks=[];
async function check(name,condition){if(!condition)throw Error(name);checks.push({name,pass:true});}
async function pause(){await page.waitForTimeout(1200)}
try{
 await page.goto('http://127.0.0.1:18765/');
 await check('unauthenticated user sees token login',await page.getByLabel('本地访问令牌',{exact:true}).isVisible());
 await page.getByLabel('本地访问令牌',{exact:true}).fill(tokens.employee);
 await page.getByRole('button',{name:'安全进入 →',exact:true}).click();
 await page.waitForFunction(()=>!document.getElementById('workspace').hidden);
 await check('employee role shown',await page.locator('#roleLabel').innerText()==='个人工作台');
 await check('no browser storage of token',await page.evaluate(()=>localStorage.length===0&&sessionStorage.length===0));
 await page.screenshot({path:path.join(output,'employee-desktop.png'),fullPage:true});
 await page.getByRole('button',{name:'◷ 会议将近',exact:true}).click();await pause();
 await check('new meeting produces alert and approval',await page.locator('#alerts .alert').count()===1&&await page.locator('#actions .action').count()===1);
 await page.getByRole('button',{name:'批准 · 保存本地',exact:true}).click();await pause();
 await check('approval writes one local outbox',await page.locator('#outboxSummary').innerText()==='查看本地 outbox · 1 条');
 await page.getByRole('button',{name:'⚑ 项目阻塞',exact:true}).click();await pause();
 await check('blocked scenario adds another explained alert',await page.locator('#alerts .alert').count()===2);
 await page.getByRole('button',{name:'⚑ 项目阻塞',exact:true}).click();await pause();
 await check('unchanged blocked evidence does not spam alerts',await page.locator('#alerts .alert').count()===2);
 await page.getByRole('button',{name:'◌ 专注与休息',exact:true}).click();await pause();
 await check('focus state visible and pauses reminders',(await page.locator('#agentStatus').innerText()).includes('专注中'));
 await page.getByRole('button',{name:'结束专注 / 检查休息提醒',exact:true}).click();await pause();
 await check('resuming focus surfaces rest recommendation',await page.locator('#alerts .rest').count()===1);
 await page.locator('#privacyToggle').click();await pause();
 await check('physical privacy simulation blocks touch',await page.locator('#touchButton').isDisabled());
 await page.screenshot({path:path.join(output,'employee-privacy.png'),fullPage:true});
 await page.locator('#privacyToggle').click();await pause();
 const ep=await ctx.newPage();
 await ep.goto('http://127.0.0.1:18765/');await ep.getByLabel('本地访问令牌',{exact:true}).fill(tokens.enterprise);await ep.getByRole('button',{name:'安全进入 →',exact:true}).click();await ep.waitForFunction(()=>!document.getElementById('workspace').hidden);
 await check('enterprise sees only result summary',await ep.locator('#employeeView').isHidden()&&await ep.locator('#enterpriseSummary .metric').count()===4);
 await ep.screenshot({path:path.join(output,'enterprise-authorized.png'),fullPage:true});
 await page.locator('#consentToggle').click();await pause();
 await ep.bringToFront();await ep.waitForFunction(()=>!!document.querySelector('.enterprise-suppressed'));
 await check('revocation hides cohort below five',await ep.locator('.enterprise-suppressed').isVisible());
 await ep.screenshot({path:path.join(output,'enterprise-revoked.png'),fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:path.join(output,'employee-mobile.png'),fullPage:true});
 await check('mobile no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await check('no frontend exceptions',errors.length===0);
 await fs.writeFile(path.join(output,'report.json'),JSON.stringify({browser:await browser.version(),isolated_headless:true,synthetic:true,checks,errors},null,2));
 console.log(JSON.stringify({status:'pass',checks:checks.length,browser:await browser.version()}));
}catch(e){await page.screenshot({path:path.join(output,'failure.png'),fullPage:true});await fs.writeFile(path.join(output,'report.json'),JSON.stringify({status:'failed',checks,error:e.message,errors},null,2));throw e;}
finally{await ctx.close();await browser.close();}
