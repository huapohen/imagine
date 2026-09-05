#pragma once
#include "protocol.hpp"
namespace lingban {
struct BoardPins{
    int red=-1,green=-1,blue=-1,touch=-1,sda=-1,scl=-1,privacy=-1,address=-1;
    uint32_t threshold=0;
};
// Hal is implemented by ArduinoHal and the native mock. No GPIO policy lives outside this controller.
template<class Hal> class Controller{
public:
    Device& device;Hal& hal;BoardPins pins;
    bool active=false,wire=false,pwm=false,screen=false;
    bool lowSeen=false;uint32_t lowSince=0,lastDraw=0;
    Controller(Device& d,Hal& h,BoardPins p):device(d),hal(h),pins(p){}
    bool rawPrivacy(){return pins.privacy<0||hal.readPrivacy(pins.privacy);}
    void input(int p){if(p>=0)hal.input(p);}
    void quiesce(){
        if(pwm){hal.pwmDetach(pins.red);hal.pwmDetach(pins.green);hal.pwmDetach(pins.blue);pwm=false;}
        if(wire){hal.wireEnd();wire=false;}
        input(pins.red);input(pins.green);input(pins.blue);input(pins.sda);input(pins.scl);input(pins.touch);
        active=false;screen=false;
    }
    bool guard(){
        if(rawPrivacy()){
            lowSeen=false;device.physicalPrivacy(true);
            if(active||wire||pwm)quiesce();
            return false;
        }
        return !device.privacy;
    }
    void begin(uint32_t now){
        // External 10k pullup on GPIO10; INPUT must not enable internal pullups on SW3V3 pins.
        input(pins.privacy);bool priv=rawPrivacy();device.physicalPrivacy(true);quiesce();
        lowSeen=!priv;lowSince=now;
        device.hasLed=pins.red>=0&&pins.green>=0&&pins.blue>=0;
        device.hasTouch=pins.touch>=0&&pins.threshold>0;
        device.hasPrivacy=pins.privacy>=0;
        // CAPS screen=1 denotes configured candidate driver, not successful physical validation.
        device.hasScreen=pins.sda>=0&&pins.scl>=0&&pins.address>=0;
    }
    bool restore(){
        if(!guard())return false;
        active=true;
        if(device.hasLed){
            pwm=true;
            const int leds[]={pins.red,pins.green,pins.blue};
            for(int i=0;i<3;i++){
                if(!guard())return false;
                hal.pwmPrepare(i,255); // Preload OFF before attaching common-anode sink output.
                if(!guard())return false;
                hal.outputHigh(leds[i]);
                if(!guard())return false;
                hal.pwmAttach(leds[i],i);
            }
        }
        if(device.hasScreen){
            if(!guard())return false;
            wire=true;bool begun=hal.wireBegin(pins.sda,pins.scl);
            if(!guard())return false;
            if(begun)screen=hal.screenInit(pins.address);
            if(!guard())return false;
            if(!screen){hal.wireEnd();wire=false;input(pins.sda);input(pins.scl);}
        }
        return true;
    }
    void step(uint32_t now){
        bool priv=rawPrivacy();
        if(priv){lowSeen=false;device.physicalPrivacy(true);if(active||wire||pwm)quiesce();}
        else if(device.privacy){
            if(!lowSeen){lowSeen=true;lowSince=now;}
            if(uint32_t(now-lowSince)>=40)device.physicalPrivacy(false);
        }
        device.poll(now);
        if(device.privacy)return;
        if(!device.ready){
            if(active){
                // Power is still on; blank OLED before releasing the bus. Never write on privacy entry.
                if(screen&&guard())hal.screenBlank();
                if(active)quiesce();
            }
            return;
        }
        if(!active&&!restore())return;
        if(pwm){
            unsigned bright[3]={0,0,0};
            if(device.led=="teal"){bright[1]=60;bright[2]=38;}
            else if(device.led=="amber"){bright[0]=70;bright[1]=30;}
            else if(device.led=="blue"){bright[1]=18;bright[2]=70;}
            for(int i=0;i<3;i++){if(!guard())return;hal.pwmWrite(i,255-bright[i]);}
        }
        if(device.hasTouch&&guard())device.physicalTouch(hal.touchPressed(pins.touch,pins.threshold,now));
        if(screen&&uint32_t(now-lastDraw)>=250&&guard()){
            hal.screenDraw(device.led);lastDraw=now;guard();
        }
    }
};
}
