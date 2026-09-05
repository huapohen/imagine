#include <Arduino.h>
#include <Wire.h>
#include "board_config.hpp"
#include "controller.hpp"

struct ArduinoHal{
    bool touchSample=false,touchStable=false;uint32_t touchEdge=0;
    bool readPrivacy(int pin){return digitalRead(pin)!=LOW;}
    void input(int pin){pinMode(pin,INPUT);if(pin==LB_PIN_TOUCH){touchSample=false;touchStable=false;}}
    void outputHigh(int pin){digitalWrite(pin,HIGH);pinMode(pin,OUTPUT);}
    void pwmPrepare(int channel,int duty){ledcSetup(channel,5000,8);ledcWrite(channel,duty);}
    void pwmAttach(int pin,int channel){ledcAttachPin(pin,channel);}
    void pwmDetach(int pin){ledcDetachPin(pin);}
    void pwmWrite(int channel,int duty){ledcWrite(channel,duty);}
    bool wireBegin(int sda,int scl){bool ok=Wire.begin(sda,scl);Wire.setClock(100000);Wire.setTimeOut(5);return ok;}
    void wireEnd(){Wire.end();}
    // Bound each I2C transaction. Recheck the physical contact before every transfer.
    bool powered(){return LB_PIN_PRIVACY>=0&&digitalRead(LB_PIN_PRIVACY)==LOW;}
    bool command(uint8_t c){
        if(!powered())return false;
        Wire.beginTransmission(LB_SCREEN_ADDRESS);Wire.write(0x00);Wire.write(c);return Wire.endTransmission()==0;
    }
    bool screenInit(int address){
        if(!powered())return false;
        Wire.beginTransmission(address);if(Wire.endTransmission()!=0)return false;
        const uint8_t init[]={0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0,0x40,0x8D,0x14,0x20,0,0xA1,0xC8,0xDA,0x12,0x81,0x7F,0xD9,0xF1,0xDB,0x40,0xA4,0xA6};
        for(uint8_t c:init)if(!command(c))return false;
        // Display stays OFF until the first fresh frame has been drawn.
        return true;
    }
    void screenBlank(){command(0xAE);}
    void screenDraw(const std::string& led){
        uint8_t pixels[1024]={0};
        auto dot=[&](int x,int y){if(x>=0&&x<128&&y>=0&&y<64)pixels[x+(y/8)*128]|=uint8_t(1<<(y%8));};
        auto box=[&](int x,int y,int w,int h){for(int a=x;a<x+w;a++)for(int b=y;b<y+h;b++)if(a==x||a==x+w-1||b==y||b==y+h-1)dot(a,b);};
        box(36,26,56,30);box(30,16,18,40);box(80,16,18,40);box(55,8,18,48);box(60,43,8,13);
        int bars=led=="off"?0:led=="teal"?2:led=="blue"?3:4;
        for(int i=0;i<bars;i++)box(107,48-i*10,10,7);
        for(uint8_t c:{0x21,0,127,0x22,0,7})if(!command(c))return;
        for(int i=0;i<1024;i+=16){
            if(!powered())return;
            Wire.beginTransmission(LB_SCREEN_ADDRESS);Wire.write(0x40);Wire.write(pixels+i,16);
            if(Wire.endTransmission()!=0)return;
        }
        command(0xAF);
    }
    bool touchPressed(int pin,uint32_t threshold,uint32_t now){
        bool sample=touchRead(pin)>threshold;
        if(sample!=touchSample){touchSample=sample;touchEdge=now;}
        if(uint32_t(now-touchEdge)>=40)touchStable=sample;
        return touchStable;
    }
};
lingban::BoardPins boardPins(){
    lingban::BoardPins p;p.red=LB_PIN_LED_R;p.green=LB_PIN_LED_G;p.blue=LB_PIN_LED_B;p.touch=LB_PIN_TOUCH;
    p.sda=LB_PIN_SDA;p.scl=LB_PIN_SCL;p.privacy=LB_PIN_PRIVACY;p.address=LB_SCREEN_ADDRESS;p.threshold=LB_TOUCH_THRESHOLD;return p;
}
lingban::Device device;ArduinoHal hal;
lingban::Controller<ArduinoHal> controller(device,hal,boardPins());
std::string incoming;bool dropping=false;uint32_t lastInput=0;
void setup(){
    controller.begin(millis()); // Read physical privacy before any screen/PWM initialization.
    // CDC_ON_BOOT=0: Serial is UART0, RX44/TX43, connected to the board's USB-UART bridge.
    Serial.begin(115200,SERIAL_8N1,44,43);
}
void loop(){
    controller.step(millis());
    // Bound serial work per pass so a continuous input stream cannot starve the privacy poll.
    unsigned budget=64;
    while(budget--&&Serial.available()){
        controller.step(millis());char c=char(Serial.read());lastInput=millis();
        if(c=='\n'){
            if(!dropping){incoming+=c;auto reply=device.receive(incoming,millis());controller.step(millis());if(!reply.empty())Serial.print(reply.c_str());}
            incoming.clear();dropping=false;
        }else if(!dropping){incoming+=c;if(incoming.size()>=lingban::MAX_FRAME){incoming.clear();dropping=true;}}
    }
    if((!incoming.empty()||dropping)&&uint32_t(millis()-lastInput)>=1000){incoming.clear();dropping=false;}
    delay(1);
}
