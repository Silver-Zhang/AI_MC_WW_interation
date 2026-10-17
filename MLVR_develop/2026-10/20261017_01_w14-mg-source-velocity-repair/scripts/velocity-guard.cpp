#include "GlobeFun.h"
#include <limits>
#include <iostream>
#include <stdexcept>
#include <cassert>
int main() {
  const double nan=std::numeric_limits<double>::quiet_NaN(), inf=std::numeric_limits<double>::infinity();
  const std::vector<double> centers={7.60695e-8,.6615,16.};
  int rejected=0;
  auto bad=[&](double g,int G,const std::vector<double>& c) {
    try { (void)CDGlobeFun::GetNeuVelMg(g,G,c); }
    catch(const std::invalid_argument&) {++rejected;return;}
    throw std::runtime_error("invalid velocity input accepted");
  };
  for(double g:{nan,inf,-inf,0.,-1.,4.,1.5,1e100}) bad(g,3,centers);
  bad(1.,0,{}); bad(1.,-1,centers);bad(1.,2,centers);bad(1.,4,centers);
  bad(1.,1,{nan});bad(1.,1,{inf});bad(1.,1,{0.});bad(1.,1,{-1.});
  const double expected[]={54.631090366073,11.243664633567,0.0038148500266633};
  for(int g=1;g<=3;++g) {
    const double v=CDGlobeFun::GetNeuVelMg(g,3,centers);
    assert(std::abs(v/expected[g-1]-1)<1e-12);
  }
  std::cout<<"invalid inputs rejected "<<rejected<<"/16; valid groups 3/3\n";
}
