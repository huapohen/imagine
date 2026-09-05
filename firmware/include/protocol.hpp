#pragma once
#include <cstdint>
#include <cstdio>
#include <string>
#include <map>
#include <deque>

namespace lingban {
static const size_t MAX_FRAME=256;
static const uint32_t OFFLINE_MS=5000;
inline uint16_t crc16(const std::string& data){
    uint16_t crc=0xffff;
    for(unsigned char c:data){crc^=uint16_t(c)<<8;for(int i=0;i<8;i++)crc=crc&0x8000?uint16_t((crc<<1)^0x1021):uint16_t(crc<<1);}
    return crc;
}
inline bool typeOK(const std::string& t){return t=="HELLO"||t=="CAPS"||t=="SET"||t=="GET"||t=="STATE"||t=="ACK"||t=="ERR"||t=="PING";}
inline bool payloadOK(const std::string& p){
    for(char c:p)if(!((c>='a'&&c<='z')||(c>='A'&&c<='Z')||(c>='0'&&c<='9')||c=='_'||c=='='||c==';'||c==','||c=='.'||c=='-'))return false;
    return true;
}
inline std::string encode(unsigned seq,const std::string& kind,const std::string& payload=""){
    if(seq<1||seq>65535||!typeOK(kind)||!payloadOK(payload))return "";
    std::string base="LB1|"+std::to_string(seq)+"|"+kind+"|"+payload;
    char crc[8];std::snprintf(crc,sizeof(crc),"|%04X\n",crc16(base));base+=crc;
    return base.size()<=MAX_FRAME?base:"";
}
struct Frame{unsigned seq=0;std::string kind,payload;};
inline bool decode(const std::string& line,Frame& f){
    if(line.size()>MAX_FRAME||line.size()<13||line.back()!='\n'||line.substr(0,4)!="LB1|")return false;
    size_t a=line.find('|',4),b=line.find('|',a==std::string::npos?line.size():a+1),c=line.find('|',b==std::string::npos?line.size():b+1);
    if(a==std::string::npos||b==std::string::npos||c==std::string::npos)return false;
    std::string s=line.substr(4,a-4);if(s.empty()||s.size()>5||s[0]=='0')return false;
    unsigned n=0;for(char d:s){if(d<'0'||d>'9')return false;n=n*10+unsigned(d-'0');}
    Frame value;value.seq=n;value.kind=line.substr(a+1,b-a-1);value.payload=line.substr(b+1,c-b-1);
    if(encode(n,value.kind,value.payload)!=line)return false;
    f=value;return true;
}
inline bool fields(const std::string& p,std::map<std::string,std::string>& out){
    if(p.empty())return true;
    size_t pos=0;
    while(pos<p.size()){
        size_t end=p.find(';',pos);if(end==std::string::npos)end=p.size();
        std::string pair=p.substr(pos,end-pos);size_t eq=pair.find('=');
        if(eq==std::string::npos||eq==0||pair.find('=',eq+1)!=std::string::npos)return false;
        std::string key=pair.substr(0,eq);if(out.count(key))return false;
        out[key]=pair.substr(eq+1);pos=end+1;if(end<p.size()&&pos==p.size())return false;
    }
    return true;
}
inline bool lowerHex(const std::string& s){for(char c:s)if(!((c>='0'&&c<='9')||(c>='a'&&c<='f')))return false;return true;}
// Strict UTF-8 Unicode scalar values (including U+0000); no overlong, surrogate or > U+10FFFF.
inline bool utf8hex(const std::string& s){
    if(s.size()>160||s.size()%2||!lowerHex(s))return false;
    std::string bytes;
    auto nibble=[](char c){return c<='9'?c-'0':c-'a'+10;};
    for(size_t i=0;i<s.size();i+=2)bytes+=char(nibble(s[i])*16+nibble(s[i+1]));
    for(size_t i=0;i<bytes.size();){
        unsigned c=static_cast<unsigned char>(bytes[i++]),cp=0,min=0;int count=0;
        if(c<=0x7f)continue;
        if(c>=0xc2&&c<=0xdf){cp=c&31;count=1;min=0x80;}
        else if(c>=0xe0&&c<=0xef){cp=c&15;count=2;min=0x800;}
        else if(c>=0xf0&&c<=0xf4){cp=c&7;count=3;min=0x10000;}
        else return false;
        while(count--){if(i==bytes.size())return false;unsigned b=static_cast<unsigned char>(bytes[i++]);if((b&0xc0)!=0x80)return false;cp=(cp<<6)|(b&63);}
        if(cp<min||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))return false;
    }
    return true;
}
struct Cached{unsigned seq;std::string frame,reply;};
class Device{
public:
    bool ready=false,privacy=true,touch=false;
    bool hasLed=false,hasTouch=false,hasPrivacy=false,hasScreen=false,simulated=false;
    std::string led="off",screen,session;
    unsigned applied=0;
    uint32_t lastHeartbeat=0;
    std::deque<Cached> cache;
    void clearOutputs(){led="off";screen.clear();touch=false;}
    void offline(){ready=false;session.clear();cache.clear();clearOutputs();}
    void poll(uint32_t now){if(ready&&uint32_t(now-lastHeartbeat)>=OFFLINE_MS)offline();}
    void physicalPrivacy(bool enabled){if(privacy!=enabled){cache.clear();clearOutputs();}privacy=enabled;if(privacy)clearOutputs();}
    void physicalTouch(bool enabled){touch=enabled&&!privacy&&ready;}
    std::string status()const{return std::string("link=")+(ready?"online":"offline")+";led="+led+";privacy="+(privacy?"1":"0")+";touch="+(touch?"1":"0")+";text="+screen;}
    std::string receive(const std::string& raw,uint32_t now=0){
        poll(now);Frame f;if(!decode(raw,f))return "";
        std::map<std::string,std::string> data;
        bool parsed=fields(f.payload,data);
        bool hello=parsed&&data.count("versions")&&data.at("versions")=="1"&&(data.size()==1||(data.size()==2&&data.count("session")&&data.at("session").size()==16&&lowerHex(data.at("session"))));
        if(f.kind=="HELLO"&&hello){
            std::string incomingSession=data.count("session")?data.at("session"):"";
            if(!ready||incomingSession!=session){cache.clear();clearOutputs();session=incomingSession;ready=false;}
        }
        for(const auto& old:cache)if(old.seq==f.seq){
            if(old.frame!=raw)return encode(f.seq,"ERR","code=sequence_conflict");
            // Reads must reflect current touch/privacy, even on a transport retry.
            if((f.kind=="GET"||f.kind=="PING")&&parsed&&data.empty())break;
            return old.reply; // Duplicate HELLO/SET does not renew the heartbeat.
        }
        std::string err,reply;
        if(!parsed)err="fields";
        else if(f.kind=="HELLO"){
            if(!hello)err="version";
            else{ready=true;lastHeartbeat=now;reply=encode(f.seq,"CAPS",std::string("version=1;led=")+(hasLed?"1":"0")+";touch="+(hasTouch?"1":"0")+";privacy="+(hasPrivacy?"1":"0")+";screen="+(hasScreen?"1":"0")+";simulated="+(simulated?"1":"0"));}
        }else if(f.kind=="GET"||f.kind=="PING"){
            if(!data.empty())err="fields";
            else{if(ready)lastHeartbeat=now;reply=f.kind=="GET"?encode(f.seq,"STATE",status()):encode(f.seq,"ACK",ready?"alive=1":"alive=0");}
        }else if(f.kind=="SET"){
            if(!ready)err="handshake_required";
            else if(privacy)err="privacy_active";
            else{
                if(data.empty()||data.size()>2)err="fields";
                for(const auto& kv:data)if(kv.first!="led"&&kv.first!="text")err="fields";
                if(err.empty()&&data.count("led")&&data["led"]!="off"&&data["led"]!="teal"&&data["led"]!="amber"&&data["led"]!="blue")err="led";
                if(err.empty()&&data.count("text")&&!utf8hex(data["text"]))err="text";
                if(err.empty()){if(data.count("led"))led=data["led"];if(data.count("text"))screen=data["text"];applied++;reply=encode(f.seq,"ACK","applied=1");}
            }
        }else err="unsupported";
        if(!err.empty())reply=encode(f.seq,"ERR","code="+err);
        // FIFO of last 16 distinct sequence IDs. Retries do not extend the window.
        for(auto& old:cache)if(old.seq==f.seq){old.reply=reply;return reply;}
        cache.push_back({f.seq,raw,reply});if(cache.size()>16)cache.pop_front();return reply;
    }
};
}
