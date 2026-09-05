import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const modules=process.env.IMAGINE_NODE_MODULES||'/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const {chromium}=createRequire(path.join(modules,'_resolver.cjs'))('playwright');
const browser=await chromium.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1050}});
const checks=[],errors=[];
page.on('pageerror',e=>errors.push(e.message));
function check(name,ok){if(!ok)throw Error(name);checks.push({name,pass:true});}
try{
 await page.goto('http://127.0.0.1:8766/',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));
 check('actual CAD hero loaded',await page.locator('.hero-art img').getAttribute('src')==='hardware/renders/lingban_hero.png');
 check('three document groups present',await page.locator('.card').count()===3);
 check('final pitch and factory links present',await page.locator('a[href="pitch/deliverables/final-20260906/lingban-vc-deck.pptx"]').count()>0&&await page.locator('a[href="hardware/delivery/lingban_factory_review.zip"]').count()>0);
 await page.waitForFunction(()=>[...document.querySelectorAll('video')].every(v=>v.readyState>=1),null,{timeout:30000});
 const media=await page.locator('video').evaluateAll(vs=>vs.map(v=>({file:v.getAttribute('src'),duration:v.duration,width:v.videoWidth,height:v.videoHeight})));
 check('all ten delivered videos have playable metadata',media.length===10&&media.every(v=>v.width>0&&Number.isFinite(v.duration)));
 check('eight native 2K fifteen second concepts',media.filter(v=>/final\/0/.test(v.file)&&v.width===2560&&v.height===1440&&Math.abs(v.duration-15)<.01).length===8);
 check('120 second reel and 28 second real demo',media.some(v=>v.file.includes('2min')&&Math.abs(v.duration-120)<.01)&&media.some(v=>v.file.includes('/demo/')&&Math.abs(v.duration-28)<.01));
 await page.screenshot({path:path.join(root,'docs/verification/portal-desktop.png')});
 await page.setViewportSize({width:390,height:844});
 check('mobile portal has no horizontal overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.screenshot({path:path.join(root,'docs/verification/portal-mobile.png')});
 check('no portal script exceptions',errors.length===0);
 await fs.writeFile(path.join(root,'docs/verification/portal-browser.json'),JSON.stringify({status:'pass',browser:await browser.version(),checks,media,errors},null,2)+'\n');
 console.log(JSON.stringify({status:'pass',checks:checks.length,videos:media.length}));
}finally{await browser.close();}
