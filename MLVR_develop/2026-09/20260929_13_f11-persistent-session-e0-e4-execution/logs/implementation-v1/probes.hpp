#pragma once
#include <string>
#if defined(RMC_F11_REUSE_EXPERIMENT) && !defined(RMC_F11_PROBE)
#error reuse requires probes
#endif
#if defined(USE_MPI) || defined(USE_OMP) || defined(AIS)
#error F11 scope requires serial standard MGACE
#endif
class CDFixedSource; class CDAceData; class CDParticleState; class CDTally;
class CDRNG; class CDExternalSource; class CDGeometry; class CDMaterial;
namespace f11_probe {
void mark(const char*); void begin(const char*); void end(const char*); void flush();
struct Scope { const char* name; explicit Scope(const char* n):name(n){begin(n);} ~Scope(){end(name);} };
void bind_model(const CDGeometry&, const CDMaterial&);
void snapshot(const char*,const CDFixedSource&,const CDAceData&,const CDParticleState&,const CDTally&,const CDRNG&,const CDExternalSource&);
void history(const CDFixedSource&,const CDRNG&);
void particle_context(const CDParticleState&);
void ww_lookup(int,int,double,int,double,double,double);
void set_run(const std::string&);
void arm(const CDFixedSource&, const CDAceData&,const CDParticleState&,const CDTally&,const CDRNG&, const CDExternalSource&);
bool consume_prepared_state_token();
void require(bool,const char*);
}
