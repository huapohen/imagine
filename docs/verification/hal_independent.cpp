#include "controller.hpp"
#include <cassert>
#include <iostream>
#include <map>
#include <string>
#include <vector>
struct Mock {
 bool privacy=true,bus=false,flipOnPrepare=false;int writes=0,draws=0,blanks=0,touches=0,ends=0;
 std::map<int,std::string> modes;std::map<int,int> duties;std::vector<std::string> events;
 bool readPrivacy(int){events.push_back("read");return privacy;}
 void input(int p){modes[p]="input";events.push_back("input");}
 void outputHigh(int p){assert(!privacy);modes[p]="high";events.push_back("high");}
 void pwmPrepare(int c,int d){assert(!privacy&&d==255);duties[c]=d;if(flipOnPrepare)privacy=true;}
 void pwmAttach(int p,int c){assert(!privacy&&duties[c]==255);modes[p]="pwm";events.push_back("attach");}
 void pwmDetach(int p){modes[p]="detached";}
 void pwmWrite(int c,int d){assert(!privacy);duties[c]=d;++writes;}
 bool wireBegin(int,int){assert(!privacy);bus=true;return true;}
 void wireEnd(){bus=false;++ends;}
 bool screenInit(int){assert(!privacy&&bus);return true;}
 void screenBlank(){assert(!privacy&&bus);++blanks;}
 void screenDraw(const std::string&){assert(!privacy&&bus);++draws;}
 bool touchPressed(int,uint32_t,uint32_t){assert(!privacy);++touches;return true;}
};
lingban::BoardPins evt(){lingban::BoardPins p;p.red=4;p.green=5;p.blue=6;p.touch=7;p.sda=8;p.scl=9;p.privacy=10;p.address=0x3c;return p;}
void inputs(const Mock& h){for(int p:{4,5,6,7,8,9})assert(h.modes.at(p)=="input");assert(!h.bus);}
int main(){
 using namespace lingban;
 {
  Device d;Mock h;Controller<Mock> c(d,h,BoardPins{});c.begin(0);
  d.receive(encode(1,"HELLO","versions=1"),0);c.step(100);
  assert(d.privacy&&!c.active&&h.writes==0&&!h.bus&&h.modes.empty());
 }
 {
  Device d;Mock h;Controller<Mock> c(d,h,evt());c.begin(0);inputs(h);
  assert(h.events.size()>1&&h.events[1]=="read");
  d.receive(encode(1,"HELLO","versions=1"),0);c.step(300);inputs(h);assert(h.writes==0&&h.draws==0);
  h.privacy=false;c.step(301);c.step(340);assert(d.privacy&&!c.active);c.step(341);
  assert(!d.privacy&&c.active&&h.bus);for(int i=0;i<3;++i)assert(h.duties[i]==255);
  d.receive(encode(2,"SET","led=teal"),350);c.step(350);
  assert(h.duties[0]==255&&h.duties[1]==195&&h.duties[2]==217&&h.touches==0);
  int oldWrites=h.writes,oldDraws=h.draws;h.privacy=true;c.step(351);inputs(h);
  assert(d.privacy&&!c.active&&h.writes==oldWrites&&h.draws==oldDraws&&h.ends==1);
  c.step(900);assert(h.writes==oldWrites&&h.draws==oldDraws);
  h.privacy=false;c.step(901);c.step(941);assert(c.active);for(int i=0;i<3;++i)assert(h.duties[i]==255);
  d.receive(encode(3,"GET"),1000);d.receive(encode(4,"SET","led=amber"),1001);c.step(5999);assert(c.active);
  c.step(6000);inputs(h);assert(!d.ready&&!c.active&&d.led=="off"&&d.screen.empty()&&h.blanks==1);
  assert(d.receive(encode(5,"SET","led=blue"),6001).find("handshake_required")!=std::string::npos);
  d.receive(encode(6,"HELLO","versions=1;session=0123456789abcdef"),6002);c.step(6002);assert(c.active);
 }
 {
  Device d;Mock h;h.privacy=false;h.flipOnPrepare=true;Controller<Mock> c(d,h,evt());c.begin(0);
  d.receive(encode(1,"HELLO","versions=1"),0);c.step(40);inputs(h);
  assert(d.privacy&&!c.active&&h.writes==0&&h.draws==0);
 }
 {
  Device d;d.physicalPrivacy(false);const uint32_t start=0xffffff00u;
  d.receive(encode(1,"HELLO","versions=1"),start);d.poll(uint32_t(start+4999));assert(d.ready);
  d.poll(uint32_t(start+5000));assert(!d.ready);
 }
 std::cout<<"Independent HAL PASS: boot privacy, safe profile, 40ms release, common-anode off/colors, immediate high-Z, I2C shutdown, disabled touch, 5s fail-safe/recovery, privacy-edge guard, millis rollover\n";
}
