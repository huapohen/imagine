import copy, importlib.util, json, pathlib, shutil, sys, tempfile, unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('video_client',pathlib.Path(__file__).with_name('video_client.py'))
v=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(v)
BASE=pathlib.Path(__file__).resolve().parent
class GuardTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)
  for name in ('sources.json','pricing-paygo.md','requests.json'):shutil.copy(BASE/name,self.root/name)
  self.old=(v.ROOT,v.LEDGER);v.ROOT=self.root;v.LEDGER=self.root/'video_ledger.json'
  self.payload=json.loads((self.root/'requests.json').read_text())[0]['payload']
 def tearDown(self):v.ROOT,v.LEDGER=self.old;self.temp.cleanup()
 def invoke(self,*args):
  with patch.object(sys,'argv',['video_client.py',*args]),patch.dict(v.os.environ,{'MINIMAX_API_KEY':'unit-test-fake-only'}):v.main()
 def test_exact_authorization_price(self):self.assertEqual(v.price(self.payload),v.D('12'))
 def test_unknown_or_mismatched_price_rejected(self):
  with (self.root/'pricing-paygo.md').open('a') as f:f.write('\nchanged')
  with self.assertRaises(ValueError):v.price(self.payload)
 def test_extra_paid_features_refused(self):
  for item in ({'type':'video_url','video_url':{'url':'https://example.com/a.mp4'}},{'type':'audio_url','audio_url':{'url':'https://example.com/a.mp3'}}):
   payload=copy.deepcopy(self.payload);payload['content'].append(item)
   with self.assertRaises(ValueError):v.price(payload)
 def test_free_reference_image(self):
  self.payload['content'].append({'type':'image_url','role':'first_frame','image_url':{'url':'data:image/png;base64,AAAA'}});self.payload.pop('ratio')
  self.assertEqual(v.price(self.payload),v.D('12'))
 def test_failure_reserves_before_network_and_blocks_retry(self):
  def failed(*args,**kwargs):
   self.assertEqual(json.loads(v.LEDGER.read_text())['entries']['01_crystal_mouse_focus']['reserved_cny'],'12.00');raise RuntimeError('network uncertain')
  with patch.object(v,'api',side_effect=failed) as api:
   with self.assertRaises(RuntimeError):self.invoke('submit','--id','01_crystal_mouse_focus','--budget-cny','100')
   with self.assertRaises(ValueError):self.invoke('submit','--id','01_crystal_mouse_focus','--budget-cny','100')
   self.assertEqual(api.call_count,1)
 def test_budget_and_count_reject_before_network(self):
  v.save(v.LEDGER,{'budget_cny':'100','entries':{str(i):{'reserved_cny':'12.00'} for i in range(8)}})
  with patch.object(v,'api') as api:
   with self.assertRaises(ValueError):self.invoke('submit','--id','01_crystal_mouse_focus','--budget-cny','100')
   api.assert_not_called()
 def test_success_id_persisted_and_poll_failure_not_refunded(self):
  with patch.object(v,'api',return_value={'task_id':'unit-task-1'}):self.invoke('submit','--id','01_crystal_mouse_focus','--budget-cny','100')
  with patch.object(v,'api',return_value={'task':{'status':'failed'}}):self.invoke('poll','--id','01_crystal_mouse_focus')
  entry=json.loads(v.LEDGER.read_text())['entries']['01_crystal_mouse_focus'];self.assertEqual(entry['task_id'],'unit-task-1');self.assertEqual(entry['reserved_cny'],'12.00')
 def test_nonofficial_endpoint_rejected(self):
  with self.assertRaises(ValueError):v.api('POST','/v2/h3_context_ir',{})
if __name__=='__main__':unittest.main()
