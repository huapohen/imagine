"""Maintainer tool: freeze spec-authored examples using stdlib binascii as independent CRC oracle.
Not run by tests; tests consume the checked-in TSV verbatim. Never import the implementation.
"""
import binascii
from pathlib import Path
rows=[]
def wire(seq,kind,payload=''):
    base=f'LB1|{seq}|{kind}|{payload}'.encode();return base+f'|{binascii.crc_hqx(base,0xffff):04X}\n'.encode()
def status(link='offline',led='off',privacy=1,touch=0,text=''):
    return f'link={link};led={led};privacy={privacy};touch={touch};text={text}'.encode()
def add(label,op,now,argument,expected):
    rows.append('\t'.join((label,op,str(now),argument.hex() if isinstance(argument,bytes) else argument,expected.hex() if expected else '-')))
def rx(label,seq,kind,payload,expected,now=0):add(label,'RX',now,wire(seq,kind,payload),expected)
def reset():add('reset','RESET',0,'-',status())
def hello(now=0):rx('hello',1,'HELLO','versions=1',wire(1,'CAPS','version=1;led=1;touch=1;privacy=1;screen=1;simulated=0'),now)
def allow(now=0):add('allow','PRIVACY',now,'0',status('online',privacy=0))
def err(seq,code):return wire(seq,'ERR','code='+code)
reset();rx('boot_get',2,'GET','',wire(2,'STATE',status().decode()));rx('boot_ping',3,'PING','',wire(3,'ACK','alive=0'));rx('boot_set',4,'SET','led=teal',err(4,'handshake_required'))
hello();rx('privacy_denies_set',5,'SET','led=teal',err(5,'privacy_active'));allow()
rx('set_unicode',2,'SET','led=teal;text=e781b5e4bcb4',wire(2,'ACK','applied=1'))
rx('duplicate_set',2,'SET','led=teal;text=e781b5e4bcb4',wire(2,'ACK','applied=1'))
rx('sequence_conflict',2,'SET','led=blue',err(2,'sequence_conflict'))
rx('get_state',3,'GET','',wire(3,'STATE',status('online','teal',0,0,'e781b5e4bcb4').decode()))
add('touch_live','TOUCH',0,'1',status('online','teal',0,1,'e781b5e4bcb4'))
rx('cached_get_is_live',3,'GET','',wire(3,'STATE',status('online','teal',0,1,'e781b5e4bcb4').decode()))
add('privacy_clears','PRIVACY',1,'1',status('online'))
rx('old_set_not_replayed',2,'SET','led=teal;text=e781b5e4bcb4',err(2,'privacy_active'),1)
add('private_touch_blocked','TOUCH',1,'1',status('online'));allow(2)
for seq,payload,code in [(10,'','fields'),(11,'privacy=0','fields'),(12,'led=off;led=blue','fields'),(13,'led=off;','fields'),(14,'led=purple','led'),(15,'led=purple;text=ff','led'),(16,'unknown=0;text=ff','fields'),(17,'text=abc','text'),(18,'text=AA','text'),(19,'text=ff','text'),(20,'text=c080','text'),(21,'text=eda080','text'),(22,'text=f4908080','text'),(23,'text=e781','text'),(24,'text=80','text'),(25,'text='+'61'*81,'text'),(26,'led=teal;ttl_ms=5','fields')]:
    rx('invalid_'+str(seq),seq,'SET',payload,err(seq,code),3)
rx('nul_scalar_allowed',30,'SET','text=00',wire(30,'ACK','applied=1'),3)
rx('largest_scalar',31,'SET','text=f48fbfbf',wire(31,'ACK','applied=1'),3)
rx('max_80_bytes',32,'SET','text='+'61'*80,wire(32,'ACK','applied=1'),3)
rx('empty_text',33,'SET','text=',wire(33,'ACK','applied=1'),3)
rx('set_off',34,'SET','led=off',wire(34,'ACK','applied=1'),3)
rx('unknown_hello_field',35,'HELLO','versions=1;wrong=1',err(35,'version'),3)
rx('invalid_version',36,'HELLO','versions=2',err(36,'version'),3)
rx('invalid_session',37,'HELLO','versions=1;session=ABCDEF0123456789',err(37,'version'),3)
rx('reply_not_request',38,'STATE','',err(38,'unsupported'),3)
rx('get_with_fields',39,'GET','x=1',err(39,'fields'),3)
rx('ping_with_fields',40,'PING','x=1',err(40,'fields'),3)
rx('exact_256_parse',41,'SET','x'*239,err(41,'fields'),3) # 2-digit seq adds one byte.
add('over_256_drop','RX',3,wire(42,'SET','x'*240),b'')
for label,raw in [('crc_corrupt',b'LB1|43|PING||0000\n'),('no_lf',wire(43,'PING')[:-1]),('crlf',wire(43,'PING')[:-1]+b'\r\n'),('leading_zero',wire('043','PING')),('zero_seq',wire(0,'PING')),('overflow_seq',wire(65536,'PING')),('unsupported_type',wire(43,'TOUCH','value=1')),('non_ascii',b'\xff\n'),('extra_delimiter',wire(43,'SET','led=off|'))]:add(label,'RX',3,raw,b'')
# Known-good GET/PING only renew a live session. SET, CRC errors and cached HELLO do not.
reset();hello(100);allow(100)
rx('heartbeat',2,'PING','',wire(2,'ACK','alive=1'),2000)
rx('late_set',3,'SET','led=blue;text=41',wire(3,'ACK','applied=1'),6999)
add('not_yet_offline','POLL',6999,'-',status('online','blue',0,0,'41'))
add('exact_timeout','POLL',7000,'-',status(privacy=0))
rx('offline_get',4,'GET','',wire(4,'STATE',status(privacy=0).decode()),7001)
rx('offline_ping',5,'PING','',wire(5,'ACK','alive=0'),7002)
rx('offline_set',3,'SET','led=blue;text=41',err(3,'handshake_required'),7003)
rx('reconnect_same_seq',1,'HELLO','versions=1;session=aaaaaaaaaaaaaaaa',wire(1,'CAPS','version=1;led=1;touch=1;privacy=1;screen=1;simulated=0'),7004)
rx('reconnect_set',2,'SET','led=amber',wire(2,'ACK','applied=1'),7005)
rx('new_nonce_clears_state',1,'HELLO','versions=1;session=bbbbbbbbbbbbbbbb',wire(1,'CAPS','version=1;led=1;touch=1;privacy=1;screen=1;simulated=0'),7006)
rx('state_reset_on_nonce',2,'GET','',wire(2,'STATE',status('online',privacy=0).decode()),7006)
add('bad_crc_not_heartbeat','RX',12005,b'LB1|3|PING||0000\n',b'')
add('timeout_after_bad_crc','POLL',12006,'-',status(privacy=0))
reset();hello();allow()
rx('cached_hello_does_not_renew',1,'HELLO','versions=1',wire(1,'CAPS','version=1;led=1;touch=1;privacy=1;screen=1;simulated=0'),0) # allow cleared cache; this HELLO is fresh.
rx('cached_hello','1','HELLO','versions=1',wire(1,'CAPS','version=1;led=1;touch=1;privacy=1;screen=1;simulated=0'),4999)
add('cached_hello_timeout','POLL',5000,'-',status(privacy=0))
reset();hello();allow()
for seq in range(2,19):rx('fifo_'+str(seq),seq,'PING','',wire(seq,'ACK','alive=1'),seq)
rx('evicted_seq_can_reuse',2,'SET','led=teal',wire(2,'ACK','applied=1'),19)
rx('retained_seq_conflict',18,'SET','led=blue',err(18,'sequence_conflict'),20)
rx('get_renew',19,'GET','',wire(19,'STATE',status('online','teal',0).decode()),4000)
rx('cached_get_renew',19,'GET','',wire(19,'STATE',status('online','teal',0).decode()),8999)
add('get_still_online','POLL',13998,'-',status('online','teal',0))
add('get_exact_timeout','POLL',13999,'-',status(privacy=0))
path=Path(__file__).resolve().parents[2]/'docs/software/serial-golden-vectors.tsv'
path.write_text('# LB1 golden vectors: name<TAB>operation<TAB>milliseconds<TAB>input_hex_or_control<TAB>expected_hex (- = no reply)\n'+'\n'.join(rows)+'\n')
print(len(rows),'frozen golden rows')
