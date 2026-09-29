#include "probes.hpp"
#include "CalMode.h"
#include "Utility/Timer.h"
#include <ctime>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cstdint>
#include <cstring>
#include <cmath>
#include <map>
#include <cstdlib>

namespace f11_probe {
namespace {
std::string env(const char* key,const char* fallback) { const char* p=std::getenv(key);return p?p:fallback; }
bool diagnostic() { static bool b=env("F11_MODE","diagnostic")!="timing";return b; }
std::string run_id=env("F11_RUN_ID","run");
std::string prefix() { return env("F11_OUTPUT",".")+"/"+run_id; }
std::string quote(const std::string& s) { std::string r="\"";for(char c:s){if(c=='"'||c=='\\')r+='\\';if(c=='\n')r+="\\n";else r+=c;}return r+'"'; }
std::string js(const std::string& x){return quote(x);}
std::string js(const char* x){return quote(x);}
std::string js(char x){return quote(std::string(1,x));}
std::string js(double x){if(!std::isfinite(x))return quote(std::isnan(x)?"nan":(x>0?"inf":"-inf"));std::ostringstream o;o<<std::setprecision(17)<<x;return o.str();}
template<class T> std::string js(const T& x){std::ostringstream o;o<<x;return o.str();}
template<class T> std::string js(const std::vector<T>& x){std::string r="[";bool first=true;for(auto const& v:x){if(!first)r+=',';first=false;r+=js(v);}return r+"]";}
std::string js(const std::vector<bool>& x){std::string r="[";for(size_t i=0;i<x.size();++i){if(i)r+=',';r+=x[i]?"true":"false";}return r+"]";}
template<class T> std::string js(const std::set<T>& x){return js(std::vector<T>(x.begin(),x.end()));}
struct Obj {std::string s="{";bool first=true;template<class T> void add(const char* k,const T& v){raw(k,js(v));}void raw(const char*k,const std::string&v){if(!first)s+=',';first=false;s+=quote(k)+":"+v;}std::string str()const{return s+"}";}};
std::string address(const void* p){std::ostringstream o;o<<p;return o.str();}
uint64_t hash_bytes(const void*p,size_t n,uint64_t h=14695981039346656037ULL){auto b=static_cast<const unsigned char*>(p);for(size_t i=0;i<n;i++){h^=b[i];h*=1099511628211ULL;}return h;}
std::string hash_string(const std::string&s){std::ostringstream o;o<<std::hex<<hash_bytes(s.data(),s.size());return o.str();}
long long ns(){timespec t{};clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec*1000000000LL+t.tv_nsec;}
std::vector<std::string> phases, snapshots, histories;
struct Event {long long history;int particle,mesh,bin,group;double position[3],direction[3],weight,energy,internal_energy,lower,survival,upper;};
std::vector<Event> events;
Event context{};
long long history_id=0;
std::map<std::string,int> calls;
const CDGeometry* geometry=nullptr;const CDMaterial* material=nullptr;
bool armed=false, driver_active=false;
std::string rng_json(const CDRNG& cr){auto&r=const_cast<CDRNG&>(cr);Obj o;o.add("type",2);o.add("seed0",r.GetSeed0());o.add("seed",r.GetSeed());o.add("stride",r.GetStride());o.add("position",r.GetPosition());o.add("position_pre",r.GetPositionPre());return o.str();}
std::string stats_json(const CDStatisticsTester&s){Obj o;
#define ADD(x) o.add(#x,s.x)
ADD(p_cTallyType);ADD(p_nTallyToCheck);ADD(p_nBatch);ADD(p_nCyc);ADD(p_nReMax);ADD(p_nVoVMax);
ADD(p_vCurrentBatch);ADD(p_vNpsPerBatch);ADD(p_vNpsStored);ADD(p_vNonZeroNum);ADD(p_vIndexOfTallyData);
ADD(p_vSum1);ADD(p_vSum2);ADD(p_vSum3);ADD(p_vSum4);ADD(p_vAvePerCycle);ADD(p_vRePrevCycle);ADD(p_vVoVPrevCycle);
ADD(p_vTempNum);ADD(p_vTempScores);ADD(p_vGatherScores);ADD(p_vLargestScore);ADD(p_vSlope);ADD(p_vpdfx);ADD(p_vpdfy);
ADD(p_vNonZeroRe);ADD(p_vZeroRe);ADD(p_vShiftedCenter);ADD(p_vFlucMean);ADD(p_vFlucRe);ADD(p_vFlucVoV);ADD(p_vFlucShiftCenter);ADD(p_vNormFactor);ADD(p_vTotMean);
ADD(p_vTooFewParticles);ADD(p_vMeanBehaviourCheck);ADD(p_vReValueCheck);ADD(p_vReDecreaseCheck);ADD(p_vReDeRateCheck);ADD(p_vVoVValueCheck);ADD(p_vVoVDecreaseCheck);ADD(p_vVoVDeRateCheck);ADD(p_vPdfSlopeCheck);
// Wall-time-dependent data kept separately, never included in physics exact comparator.
Obj time;time.add("Time",s.p_vTime);time.add("LargestTime",s.p_vLargestTime);time.add("FoMPerCycle",s.p_vFoMPerCycle);time.add("FoMTot",s.p_vFoMTot);time.add("FlucFOM",s.p_vFlucFOM);time.add("FoMValueCheck",s.p_vFoMValueCheck);time.add("FoMBehaviourCheck",s.p_vFoMBehaviourCheck);o.raw("timing_dependent",time.str());
#undef ADD
return o.str();}
std::string particle_json(const CDParticleState&p){Obj o;o.add("role",p.p_bIsAdjointParticle);o.add("type",int(p.p_eParticleType));o.add("dirty_nuclide",p.p_vIsNucLocCellTmpChanged);o.add("cell_changed",p.p_bIsCellChanged);o.add("material_changed",p.p_bIsMatChanged);o.add("temperature_changed",p.p_bIsCellTmpChanged);o.add("density_changed",p.p_bDensIsChanged);
std::vector<std::vector<double>> cache;for(const auto&v:p.p_vONucCs){auto&c=v.p_ONucCs;cache.push_back({v.p_dNucLocCellTMP,double(v.p_nInterpPos),v.p_dInterpFrac,double(v.p_nProbTableFlag),c.p_dTot,c.p_dAbs,c.p_dEl,c.p_dInel,c.p_dFis,c.p_dNu,c.p_dN2N,c.p_dN3N});}o.add("neutron_xs_cache",cache);o.add("cache_hash_fnv1a64",hash_string(js(cache)));o.add("nearest_particle_size",p.p_vNearestParticleID.size());o.add("nearest_poisson_size",p.p_vNearestPoissonBoxID.size());o.add("real_displace",p.p_dRealDisplace);return o.str();}
}
void require(bool ok,const char*message){if(!ok){std::ofstream(prefix()+".hard-fail.txt")<<message<<'\n';flush();std::cerr<<"F11 HARD FAIL: "<<message<<'\n';std::exit(90);}}
void bind_model(const CDGeometry&g,const CDMaterial&m){geometry=&g;material=&m;}
void mark(const char*n){Obj o;o.add("run_id",run_id);o.add("kind","mark");o.add("name",n);o.add("ns",ns());phases.push_back(o.str());}
void begin(const char*n){Obj o;o.add("run_id",run_id);o.add("kind","begin");o.add("name",n);o.add("ns",ns());phases.push_back(o.str());calls[n]++;}
void end(const char*n){Obj o;o.add("run_id",run_id);o.add("kind","end");o.add("name",n);o.add("ns",ns());phases.push_back(o.str());}
void set_run(const std::string&r){require(!armed,"unconsumed prepared token");run_id=r;driver_active=true;history_id=0;phases.clear();snapshots.clear();histories.clear();events.clear();}
void history(const CDFixedSource&f,const CDRNG&r){if(!diagnostic())return;history_id=f.p_llCurParNumEachPro+1;Obj o;o.add("history",history_id);o.raw("rng",rng_json(r));histories.push_back(o.str());}
void particle_context(const CDParticleState&p){if(!diagnostic())return;context.history=history_id;context.particle=int(p.p_eParticleType);for(int i=0;i<3;++i){context.position[i]=p.p_dPos[i];context.direction[i]=p.p_dDir[i];}context.weight=p.p_dWgt;context.internal_energy=p.p_dErg;context.group=30-int(p.p_dErg+0.5);}
void ww_lookup(int type,int mesh,double energy,int bin,double low,double survive,double upper){if(!diagnostic())return;Event e=context;e.particle=type;e.mesh=mesh;e.energy=energy;e.bin=bin;e.lower=low;e.survival=survive;e.upper=upper;events.push_back(e);}
void snapshot(const char*phase,const CDFixedSource&f,const CDAceData&a,const CDParticleState&p,const CDTally&t,const CDRNG&r,const CDExternalSource&s){
if(!diagnostic())return;
Obj o;o.add("run_id",run_id);o.add("phase",phase);o.add("requested",f.p_llUserInputParNum);o.add("completed",f.p_llCurTotParNum);o.add("completed_rank",f.p_llCurParNumEachPro);o.add("finish",f.p_nFinishCalculate);o.add("starting_weight_denominator",f.p_dTotStartWgt);o.add("starting_weight_origin",f.p_dTotStartWgtOrigin);o.add("batch",f.p_llCurrentBatch);
bool initialized=std::string(phase)!="before_full_init" || calls["xs_load_and_mg_prepare"]>0;
// Fixed-source counters without constructor initializers must not be read before Init.
if(initialized){o.add("fixed_source_count",f.p_nFixedSrcCount);o.add("collisions",f.p_llTotCollisionCount);}
std::vector<size_t> banks;for(const auto&b:f.p_vFixedParticleSrcBank)banks.push_back(b.ParticleBank.size());o.add("raw_particle_stacks",banks);o.add("fixed_src_storage",f.p_vFixedSrc.size());o.add("fixed_src_bank",f.p_vFixedSrcBank.size());o.add("photon_bank",f.p_vPhotonBank.size());o.add("electron_bank",f.p_vElectronBank.size());o.add("external_neutron_bank",s.p_vFixedInitSrcBank.size());o.add("external_photon_bank",s.p_vFixedInitPhoSrcBank.size());o.add("external_neutron_count",s.p_nFixedInitSrcBankCount);o.add("external_photon_count",s.p_nFixedInitPhoSrcBankCount);
o.raw("rng",rng_json(r));o.add("fixed_adjoint",f.p_bIsAdjoint);o.add("ace_adjoint",a.p_bIsAdjoint);o.add("physical_max_adjoint_energy_MeV",f.p_bIsAdjoint?30.0:20.0);o.add("internal_cutoff",f.p_dMaxAdjointNeutronEnergy);o.add("internal_photon_cutoff",f.p_dMaxAdjointPhotonEnergy);o.raw("particle",particle_json(p));
std::vector<std::vector<std::vector<double>>> adj;std::vector<std::vector<double>> fis;std::string raw;
std::vector<std::string> nuc_ids;for(size_t i=1;i<a.p_vNuclides.size();++i){const auto&n=a.p_vNuclides[i];adj.push_back(n.p_vAdjointCrossSection);fis.push_back(n.p_vAdjointFissionCrossSection);raw+=js(n.XSS);nuc_ids.push_back(address(&n));}
o.add("adjoint_xs",adj);o.add("adjoint_fission_xs",fis);o.add("adjoint_hash_fnv1a64",hash_string(js(adj)));o.add("adjoint_fission_hash_fnv1a64",hash_string(js(fis)));o.add("raw_mgace_hash_fnv1a64",hash_string(raw));
Obj base;
if(geometry){std::vector<std::vector<double>>surfaces;for(size_t k=1;k<geometry->p_vSurface.size();++k){auto&v=geometry->p_vSurface[k];std::vector<double>row={double(v.p_nType),double(v.p_nBoundCond)};row.insert(row.end(),v.p_vParas.begin(),v.p_vParas.end());surfaces.push_back(row);}base.add("surfaces_type_bc_parameters",surfaces);std::vector<std::vector<int>>cells;for(size_t k=1;k<geometry->p_vCell.size();++k){auto&c=geometry->p_vCell[k];std::vector<int>row={c.p_nMatIndexU,c.p_nMatIndex,c.p_nFillUnivIndex};row.insert(row.end(),c.p_vBoundSurf.begin(),c.p_vBoundSurf.end());cells.push_back(row);}base.add("cells_material_fill_surfaces",cells);base.add("universe_count",geometry->p_vUniverse.size());}
if(material&&initialized){std::vector<std::vector<double>>mats;for(size_t k=1;k<material->p_vMatSet.size();++k){auto&m=material->p_vMatSet[k];std::vector<double>row={m.p_dMatUserDen,m.p_dMatAtomDen,m.p_dMatGramDen};for(auto v:m.p_vMatNucIndex)row.push_back(v);row.insert(row.end(),m.p_vMatNucAtomDen.begin(),m.p_vMatNucAtomDen.end());mats.push_back(row);}base.add("materials_density_nuclide",mats);}
o.raw("model_base",base.str());o.add("model_base_hash_fnv1a64",hash_string(base.str()));
std::vector<std::vector<double>> mesh_geometry;for(auto&m:t.p_vMeshTally){std::vector<double>v;for(int i=0;i<3;++i){v.push_back(m.p_OTallyMesh.p_nMeshNum[i]);v.push_back(m.p_OTallyMesh.p_dBoundMin[i]);v.push_back(m.p_OTallyMesh.p_dBoundMax[i]);}mesh_geometry.push_back(v);}o.add("tally_mesh_geometry",mesh_geometry);std::vector<double>wmg;for(int i=0;i<3;++i){wmg.push_back(OWeightWindow.p_OWeightWindowMesh.p_nMeshNum[i]);wmg.push_back(OWeightWindow.p_OWeightWindowMesh.p_dBoundMin[i]);wmg.push_back(OWeightWindow.p_OWeightWindowMesh.p_dBoundMax[i]);}o.add("ww_mesh_geometry",wmg);
Obj identities;identities.add("geometry",address(geometry));identities.add("material",address(material));identities.add("ace",address(&a));identities.add("nuclides",nuc_ids);identities.add("particle",address(&p));identities.add("tally",address(&t));identities.add("mesh_data",address(t.p_OMeshTallyData.p_vAve.data()));identities.add("ww",address(&OWeightWindow));identities.add("ww_mesh",address(&OWeightWindow.p_OWeightWindowMesh));identities.add("ww_energy",address(OWeightWindow.p_vEnergyBins[1].data()));o.raw("addresses",identities.str());
std::vector<std::vector<double>> sources;for(const auto&v:s.p_vSource){std::vector<double>row={double(v.p_nParticleType),v.p_dFraction,v.p_dWeight,v.p_dEnergy};row.insert(row.end(),v.p_vPoints.begin(),v.p_vPoints.end());sources.push_back(row);}o.add("sources_type_fraction_weight_energy_points",sources);o.add("source_probabilities",s.p_vFraction);o.add("source_bias_probabilities",s.p_vBiasFrac);
o.add("registry_size",t.p_pTallyDataPointer.size());std::vector<bool> registry;for(const auto* ptr:t.p_pTallyDataPointer)registry.push_back(ptr==&t.p_OMeshTallyData);o.add("registry_points_to_mesh_owner",registry);
const auto&d=t.p_OMeshTallyData;Obj tally;
#define TV(n) tally.add(#n,d.n)
TV(p_vScore);TV(p_vScoreTemp);TV(p_vSum1);TV(p_vSum2);TV(p_vAve);TV(p_vRe);TV(p_vSum3);TV(p_setScoreIndex);TV(p_vScoreIndex2);TV(p_vScoreStride);
#undef TV
tally.raw("statistics",stats_json(d.p_OStatisticsTester));o.raw("tally",tally.str());
std::vector<std::vector<double>> defs;for(const auto&m:t.p_vMeshTally){std::vector<double>v={double(m.p_nTallyID),double(m.p_nDataStartPtr),double(m.p_nDataLen)};if(initialized){v.push_back(m.p_nTotMeshNum);v.push_back(m.p_nErgBinSize);v.insert(v.end(),m.p_vErgBins.begin(),m.p_vErgBins.end());}defs.push_back(v);}o.add("mesh_definitions",defs);
o.add("mg_centres_MeV",a.p_vNeuMltCentErg);o.add("mg_lowers_MeV",a.p_vNeuMltErgBins);std::vector<double> edges=a.p_vNeuMltErgBins;if(!edges.empty())edges.push_back(2*a.p_vNeuMltCentErg.back()-edges.back());o.add("physical_edges_MeV",edges);
std::vector<std::vector<double>> nuc_centres,nuc_widths;if(a.p_nNeuMltGrpNum==30 && a.p_vNuclides.size()>1){auto&nc=const_cast<CDAceData&>(a);for(size_t k=1;k<a.p_vNuclides.size();++k){int loc=nc.GetMgNeuLERG(k);std::vector<double>c,w;for(int i=30;i>=1;--i){c.push_back(a.p_vNuclides[k].XSS[loc+i-1]);w.push_back(a.p_vNuclides[k].XSS[loc+30+i-1]);}nuc_centres.push_back(c);nuc_widths.push_back(w);}}o.add("nuclide_centres_MeV",nuc_centres);o.add("nuclide_widths_MeV",nuc_widths);
o.add("ww_energy_bins",OWeightWindow.p_vEnergyBins);o.add("ww_parameters",OWeightWindow.p_vWeightWindowPara);std::vector<std::vector<std::vector<double>>> ww;for(const auto&part:OWeightWindow.p_vMeshInformation){std::vector<std::vector<double>>rows;for(const auto&mesh:part){std::vector<double>v;for(const auto&b:mesh){v.push_back(b.p_dLowerWeightBound);v.push_back(b.p_dSurvivalWeight);v.push_back(b.p_dUpperWeightBound);}rows.push_back(v);}ww.push_back(rows);}o.add("ww_bounds",ww);
Obj counts;for(auto&v:calls)counts.add(v.first.c_str(),v.second);o.raw("cumulative_calls",counts.str());snapshots.push_back(o.str());
}
void arm(const CDFixedSource&f,const CDAceData&a,const CDParticleState&p,const CDTally&t,const CDRNG&r,const CDExternalSource&s){
#ifdef RMC_F11_REUSE_EXPERIMENT
require(driver_active&&!armed,"token only from active driver, one outstanding maximum");
require(f.p_nFinishCalculate==-1 && f.p_llCurParNumEachPro==0 && f.p_llCurTotParNum==0,"run counters not reset");
require(f.p_llUserInputParNum>100 && a.p_bIsMultiGroup && a.p_nNeuMltGrpNum==30,"unsupported run scope");
for(auto&b:f.p_vFixedParticleSrcBank)require(b.ParticleBank.empty(),"bank not empty");
require(f.p_bIsAdjoint==a.p_bIsAdjoint && p.p_bIsAdjointParticle==f.p_bIsAdjoint,"role inconsistent");
require(t.p_vMeshTally.size()==1 && t.p_pTallyDataPointer.size()==1 && t.p_pTallyDataPointer[0]==&t.p_OMeshTallyData,"registry invalid");
const auto&d=t.p_OMeshTallyData;for(const auto*v:{&d.p_vScore,&d.p_vScoreTemp,&d.p_vSum1,&d.p_vSum2,&d.p_vAve,&d.p_vRe})for(double x:*v)require(x==0,"tally not zero");
require(d.p_setScoreIndex.empty()&&d.p_vScoreIndex2.empty()&&d.p_vScoreStride.empty(),"touched indices not cleared");
auto&rg=const_cast<CDRNG&>(r);require(rg.GetPosition()==0 && rg.GetPositionPre()==-1000 && rg.GetStride()==1000000,"RNG precondition");
require(s.p_vSource.size()==1&&s.p_vSource[0].p_dWeight==1&&s.p_vSource[0].p_dFraction==1,"unit source precondition");
armed=true;mark("prepared_token.armed");
#else
require(false,"P1 is disabled in this binary");
#endif
}
bool consume_prepared_state_token(){if(!armed)return false;require(driver_active,"token without driver");armed=false;mark("prepared_token.consumed");return true;}
void metadata(const CDFixedSource&f,const CDRNG&r,const CDExternalSource&s){
Obj o;o.add("run_id",run_id);o.add("requested",f.p_llUserInputParNum);o.add("completed",f.p_llCurTotParNum);o.add("completed_rank",f.p_llCurParNumEachPro);o.add("denominator",f.p_dTotStartWgt);o.add("finish",f.p_nFinishCalculate);o.add("adjoint",f.p_bIsAdjoint);o.raw("rng",rng_json(r));o.add("component_probabilities",s.p_vFraction);o.add("component_bias_probabilities",s.p_vBiasFrac);std::vector<double>weights;for(const auto&v:s.p_vSource)weights.push_back(v.p_dWeight);o.add("initial_source_weights",weights);o.add("collector","common endpoint after CalcFixedSource/RunCalculation; no RNG calls or simulation-state writes");std::ofstream(prefix()+".run-metadata.json")<<o.str()<<'\n';
}
void flush(){
std::ofstream phase(prefix()+".timing.jsonl");for(auto&s:phases)phase<<s<<'\n';
if(!diagnostic())return;
std::ofstream snap(prefix()+".snapshots.jsonl");for(auto&s:snapshots)snap<<s<<'\n';
std::ofstream hist(prefix()+".histories.jsonl");for(auto&s:histories)hist<<s<<'\n';
std::ofstream ww(prefix()+".ww.tsv");ww<<"history\tparticle\tx\ty\tz\tu\tv\tw\tweight\tenergy_MeV\tmesh\tphysical_group0\tinternal_group\tww_bin0\tlower\tsurvival\tupper\n"<<std::setprecision(17);
for(const auto&e:events){ww<<e.history<<'\t'<<e.particle;for(auto x:e.position)ww<<'\t'<<x;for(auto x:e.direction)ww<<'\t'<<x;ww<<'\t'<<e.weight<<'\t'<<e.energy<<'\t'<<e.mesh<<'\t'<<e.group<<'\t'<<e.internal_energy<<'\t'<<e.bin<<'\t'<<e.lower<<'\t'<<e.survival<<'\t'<<e.upper<<'\n';}
}
}
