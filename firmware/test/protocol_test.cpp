#include "protocol.hpp"
#include <cassert>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
int main(int argc,char**argv){
    using namespace lingban;
    if(argc>2&&std::string(argv[1])=="--golden"){
        std::ifstream file(argv[2]);assert(file.good());Device d;std::string line;unsigned count=0;
        auto fromHex=[](const std::string& hex){std::string result;if(hex=="-")return result;for(size_t i=0;i<hex.size();i+=2)result+=char(std::stoul(hex.substr(i,2),nullptr,16));return result;};
        while(std::getline(file,line)){
            if(line.empty()||line[0]=='#')continue;
            std::vector<std::string> cols;std::istringstream row(line);std::string field;while(std::getline(row,field,'\t'))cols.push_back(field);
            assert(cols.size()==5);uint32_t now=uint32_t(std::stoul(cols[2]));std::string out;
            if(cols[1]=="RESET"){d=Device{};d.hasLed=d.hasTouch=d.hasPrivacy=d.hasScreen=true;out=d.status();}
            else if(cols[1]=="PRIVACY"){d.physicalPrivacy(cols[3]=="1");out=d.status();}
            else if(cols[1]=="TOUCH"){d.physicalTouch(cols[3]=="1");out=d.status();}
            else if(cols[1]=="POLL"){d.poll(now);out=d.status();}
            else if(cols[1]=="RX")out=d.receive(fromHex(cols[3]),now);
            else assert(false);
            if(out!=fromHex(cols[4])){std::cerr<<"golden mismatch: "<<cols[0]<<" got "<<out<<"\n";return 1;}count++;
        }
        std::cout<<"shared golden vectors PASS: "<<count<<" rows\n";return 0;
    }
    if(argc>1&&std::string(argv[1])=="--echo"){
        Device d;d.physicalPrivacy(false);std::string line;
        while(std::getline(std::cin,line)){auto reply=d.receive(line+"\n");std::cout<<(reply.empty()?"DROP\n":reply);}
        return 0;
    }
    assert(crc16("123456789")==0x29b1);
    Frame f;auto hello=encode(1,"HELLO","versions=1");assert(decode(hello,f)&&f.seq==1&&f.kind=="HELLO");
    assert(!decode("LB1|1|HELLO|versions=1|0000\n",f));assert(!decode(std::string(300,'x'),f));
    assert(!decode("LB1|0|GET||0000\n",f));assert(encode(65536,"GET").empty());assert(encode(2,"NOPE").empty());
    Device d;assert(d.privacy);assert(d.receive(encode(2,"SET","led=teal")).find("handshake_required")!=std::string::npos);
    assert(d.receive(hello).find("CAPS")!=std::string::npos);
    assert(d.receive(encode(3,"SET","led=teal")).find("privacy_active")!=std::string::npos);
    d.physicalPrivacy(false);auto frame=encode(4,"SET","led=teal;text=e781b5e4bcb4");auto reply=d.receive(frame);
    assert(reply==d.receive(frame)&&d.applied==1&&d.led=="teal");
    assert(d.receive(encode(4,"SET","led=amber")).find("sequence_conflict")!=std::string::npos);
    d.physicalTouch(true);assert(d.touch);d.physicalPrivacy(true);assert(!d.touch&&d.led=="off"&&d.screen.empty());
    assert(d.receive(encode(5,"SET","led=amber")).find("privacy_active")!=std::string::npos);
    assert(d.receive(encode(6,"SET","privacy=0")).find("ERR")!=std::string::npos);
    d.physicalPrivacy(false);
    assert(d.receive(encode(7,"SET","led=teal;led=blue")).find("fields")!=std::string::npos);
    assert(d.receive(encode(8,"SET","text=abc")).find("text")!=std::string::npos);
    assert(d.receive(encode(9,"GET")).find("STATE")!=std::string::npos);
    assert(d.receive(encode(10,"HELLO","versions=2")).find("version")!=std::string::npos);
    std::cout<<"firmware protocol self-test PASS (CRC, framing, negotiation, fail-closed privacy, dedup, conflict, fields)\n";
}
