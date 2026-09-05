#include "controller.hpp"
#include <cassert>
#include <iostream>
#include <vector>
#include <algorithm>
using namespace lingban;
struct MockHal{
    bool privacy=true,initOK=true,flipInWire=false;std::vector<std::string> calls;
    void call(const std::string& s){calls.push_back(s);}
    bool readPrivacy(int p){call("read:"+std::to_string(p));return privacy;}
    void input(int p){call("input:"+std::to_string(p));}
    void outputHigh(int p){assert(!privacy);call("high:"+std::to_string(p));}
    void pwmPrepare(int c,int d){assert(!privacy);call("prepare:"+std::to_string(c)+":"+std::to_string(d));}
    void pwmAttach(int p,int c){assert(!privacy);call("attach:"+std::to_string(p)+":"+std::to_string(c));}
    void pwmDetach(int p){call("detach:"+std::to_string(p));}
    void pwmWrite(int c,int d){assert(!privacy);call("duty:"+std::to_string(c)+":"+std::to_string(d));}
    bool wireBegin(int a,int b){assert(!privacy);call("wire.begin:"+std::to_string(a)+":"+std::to_string(b));if(flipInWire)privacy=true;return true;}
    void wireEnd(){call("wire.end");}
    bool screenInit(int a){assert(!privacy);call("screen.init:"+std::to_string(a));return initOK;}
    void screenBlank(){assert(!privacy);call("screen.blank");}
    void screenDraw(const std::string& s){assert(!privacy);call("screen.draw:"+s);}
    bool touchPressed(int p,uint32_t,uint32_t){assert(!privacy);call("touch:"+std::to_string(p));return true;}
    bool has(const std::string& s){return std::find(calls.begin(),calls.end(),s)!=calls.end();}
    size_t pos(const std::string& s){auto it=std::find(calls.begin(),calls.end(),s);assert(it!=calls.end());return size_t(it-calls.begin());}
};
BoardPins evt(){BoardPins p;p.red=4;p.green=5;p.blue=6;p.touch=7;p.sda=8;p.scl=9;p.privacy=10;p.address=0x3c;return p;}
int main(){
    Device d;MockHal h;Controller<MockHal> c(d,h,evt());c.begin(0);
    assert(h.calls[0]=="input:10"&&h.calls[1]=="read:10");assert(!h.has("wire.begin:8:9"));assert(!c.active);
    for(int p:{4,5,6,7,8,9})assert(h.has("input:"+std::to_string(p)));
    d.receive(encode(1,"HELLO","versions=1"),0);c.step(1);assert(!c.active);
    h.privacy=false;c.step(10);c.step(49);assert(!c.active);c.step(50);assert(c.active);
    assert(h.pos("prepare:0:255")<h.pos("high:4")&&h.pos("high:4")<h.pos("attach:4:0"));
    assert(h.has("duty:0:255")&&h.has("duty:1:255")&&h.has("duty:2:255"));
    assert(!h.has("touch:7")&&!d.hasTouch); // Uncalibrated threshold remains off.
    d.receive(encode(2,"SET","led=teal;text=e781b5"),60);c.step(250);
    assert(h.has("duty:1:195")&&h.has("duty:2:217")&&h.has("screen.draw:teal"));
    h.calls.clear();h.privacy=true;c.step(251);
    assert(!c.active&&d.privacy&&d.led=="off"&&d.screen.empty());
    assert(h.pos("detach:4")<h.pos("wire.end")&&h.pos("wire.end")<h.pos("input:8"));
    assert(!h.has("screen.blank")&&!h.has("screen.draw:teal"));
    for(int p:{4,5,6,7,8,9})assert(h.has("input:"+std::to_string(p)));
    h.calls.clear();c.step(1000);assert(h.calls.size()==1&&h.calls[0]=="read:10");
    h.privacy=false;c.step(1001);h.privacy=true;c.step(1020);h.privacy=false;c.step(1021);c.step(1060);assert(!c.active);c.step(1061);assert(c.active);
    assert(h.has("screen.init:60")); // Reinitialize only after a continuous allowed interval.
    d.receive(encode(3,"GET"),2000);d.receive(encode(4,"SET","led=amber;text=41"),6900);
    c.step(6999);assert(d.ready&&c.active);
    h.calls.clear();c.step(7000);assert(!d.ready&&!c.active&&d.screen.empty()&&d.led=="off");
    assert(h.pos("screen.blank")<h.pos("wire.end"));
    assert(d.receive(encode(5,"GET"),7001).find("link=offline")!=std::string::npos);
    d.receive(encode(6,"HELLO","versions=1;session=1111111111111111"),7002);c.step(7002);assert(c.active);
    // Interrupt during peripheral restore: no screenInit on a newly unpowered bus.
    Device di;MockHal hi;hi.privacy=false;hi.flipInWire=true;Controller<MockHal> ci(di,hi,evt());ci.begin(0);
    di.receive(encode(1,"HELLO","versions=1"));ci.step(40);assert(!ci.active&&di.privacy);assert(!hi.has("screen.init:60"));assert(hi.has("wire.end"));
    // Missing display ACK ends Wire and releases I2C; no refresh occurs.
    Device dn;MockHal hn;hn.privacy=false;hn.initOK=false;Controller<MockHal> cn(dn,hn,evt());cn.begin(0);dn.receive(encode(1,"HELLO","versions=1"));cn.step(40);cn.step(300);
    assert(!cn.wire&&!cn.screen&&hn.has("input:8")&&!hn.has("screen.draw:off"));
    Device ds;MockHal hs;Controller<MockHal> cs(ds,hs,BoardPins{});cs.begin(0);ds.receive(encode(1,"HELLO","versions=1"));cs.step(100);
    assert(hs.calls.empty()&&!cs.active&&ds.privacy);
    // The clock wrap interval remains 5000ms, not a signed overflow.
    Device wrap;wrap.physicalPrivacy(false);wrap.receive(encode(1,"HELLO","versions=1"),0xfffffff0u);wrap.poll(4983);assert(wrap.ready);wrap.poll(4984);assert(!wrap.ready);
    std::cout<<"controller mock HAL PASS: startup privacy, active-low PWM, high-Z/Wire/PWM order, debounce, offline, reconnect, missing screen, safe profile, millis wrap\n";
}
