# Source map

## Entrypoint and top-level lifecycle
    57	int main(int argc, char *argv[]) {
    58	  ///////////////// Define objects ////////////////////////
    59	  ///////  decoupling via refactoring at 20130720   ///////
    60	  CDRNG ORNG;
    61	  CDInput OInput;
    62	  CDGeometry OGeometry;
    63	  CDMaterial OMaterial;
    64	  CDAceData OAceData;
    65	  CDCriticality OCriticality;
    66	  CDBurnup OBurnup;
    67	  CDTally OTally;
    68	  CDConvergence OConvergence;
    69	  CDParticleState OParticleState;
    70	  CDPlot OPlot;
    71	  CDFixedSource OFixedSource;
    72	  CDExternalSource OExternalSource;
    73	  CDNeutronTransport ONeutronTransport;
    74	  CDPhotonTransport OPhotonTransport;
    75	  CDElectronTransport OElectronTransport;
    76	  CDAdjoint OAdjoint;
    77	  CDSampling OSampling;
    78	  CDKinetics OKinetics;
    79	  CDPerturbation OPerturb;
    80	
    81	  ////Classes just for PointBurnUp Mode///////
    82	  Depth_Class ODepth;
    83	  TTA_Class OTTA;
    84	  ME_Class OME;
    85	
    86	  //// Classes for group constant generation
    87	  CDGroupConstant OGroupConstant;
    88	  CDHomogenization OHomogenization;
    89	
    90	  ///////////////// Parallel Case ////////////////////////
    91	# ifdef USE_MPI
    92	  MPI_Init(&argc, &argv);
    93	  OParallel.InitiateParallel();
    94	# endif
    95	
    96	#ifdef DEBUG_ATTACH
    97	  Utility::Debug::PauseProcessToWaitForAttaching();
    98	#endif
    99	
   100	#ifdef USE_SIGHANDLER
   101	#ifdef USE_UNIX
   102	  Utility::Handler::InitSigHandler();
   103	#endif
   104	#endif
   105	
   106	#ifdef BACKTRACE
   107	  Utility::Handler::SetBACKTRACEHandler();
   108	#endif
   109	
   110	#ifdef CATCH_ERROR
   111	  Utility::Handler::SetCATCHERRORHandler();
   112	#endif
   113	
   114	#ifdef PERSONAL_USE
   115	#ifdef USE_WINDOWS
   116	  _beginthread(reinterpret_cast<void (*)(void *)>(Utility::Handler::StartAlarm), 0, NULL);
   117	#else
   118	  Utility::Handler::StartAlarm();
   119	#endif
   120	
   121	# endif
   122	
   123	  /////////Check command line and inp file exist: start ////////////
   124	  OInput.CheckIOFile(argc, argv);
   125	
   126	  /// Set Logger ///
   127	  OLogger.init_logger(Output.p_chOutputFileName);
   128	  OLogger.SetDefaultLogLevel(RMC::IO::LogLevel::info);
   129	  OLogger.SetDefaultTarget(RMC::IO::LogTarget::ConsoleAndLogFile);
   130	  OProcLogger = OLogger;
   131	  OProcLogger.SetAllowEveryProcLogging(true);
   132	
   133	  ////////////// Write output heading ////////////////
   134	  Output.OutputHeading(OCriticality);
   135	
   136	  ////////////// Write Status File ///////////////////
   137	  if (OStatus.isPrintStatus()) {
   138	    OStatus.printHeader();
   139	  }
   140	
   141	  ////////////// Read input file ////////////////
   142	  OInput.ReadInputBlocks(OCalMode, ONeutronTransport, OPhotonTransport, OElectronTransport, OGeometry,
   143	                         OMaterial, OAceData, OCriticality, OTally, OConvergence, OBurnup, OPlot,
   144	                         OFixedSource, ORNG, OAdjoint, OHomogenization, OExternalSource, OSampling,
   145	                         OKinetics, OPerturb);
   146	
   147	  ////////////// Plot Image(geometry) ////////////////
   148	  OPlot.RunPlot(OGeometry, OMaterial, ORNG);
   149	
   150	  ////////////// Generate Input File////////////////
   151	  Output.GenerateInpFile(OGeometry, OMaterial, OAceData, OCriticality, OTally, OConvergence,
   152	                         OBurnup, OFixedSource, ORNG, OPerturb);
   153	
   154	  ////////////// Run Calculation ////////////////
   155	  OCalMode.RunCalculation(OCalMode, ONeutronTransport, OPhotonTransport, OElectronTransport, OAceData,
   156	                          OGeometry, ODepth, OCriticality, OMaterial,
   157	                          OParticleState, OConvergence, OTally, OBurnup,
   158	                          OFixedSource, ORNG, OME, OTTA, OAdjoint, OExternalSource,
   159	                          OSampling, OKinetics, OPerturb);
   160	
   161	  ////////////// Write output ending ////////////////
   162	  Output.OutputEnding(OCalMode, OAdjoint, OCriticality, OFixedSource);
   163	
   164	  ///////////////// Parallel Case ////////////////////////
   165	# ifdef USE_MPI
   166	  MPI_Finalize();
   167	# endif
   168	
   169	  return 0;
   170	}

## Calculation dispatcher
RMC/src/main.cpp:155:  OCalMode.RunCalculation(OCalMode, ONeutronTransport, OPhotonTransport, OElectronTransport, OAceData,
RMC/src/CalMode.h:152:  void RunCalculation(CDCalMode &cCalMode, CDNeutronTransport cNeutronTransport, CDPhotonTransport &cPhotonTransport,
RMC/src/CalMode.h:223:  CalcFixedSource(CDCalMode &cCalMode, CDNeutronTransport &cNeutronTransport, CDPhotonTransport &cPhotonTransport,
RMC/src/CalcBurnup.cpp:34:  cCriticality.InitiateAll(cCalMode.p_nParticleMode, cNeutronTransport, cGeometry, cMaterial, cConvergence,
RMC/src/CalcFixedSource.cpp:67:void CDCalMode::CalcFixedSource(CDCalMode &cCalMode, CDNeutronTransport &cNeutronTransport,
RMC/src/CalcFixedSource.cpp:78:  cFixedSource.InitiateAll(cCalMode.p_nParticleMode, cNeutronTransport, CGeometry, CMaterial, CTally,
RMC/src/CalcCriticality.cpp:31:  cCriticality.InitiateAll(cCalMode.p_nParticleMode, cNeutronTransport, cGeometry, cMaterial, cConvergence,
RMC/src/CalcKinetics.cpp:9:  cKinetics.InitiateAll(cNeutronTransport, cGeometry, cMaterial, cTally, cAceData, cParticleState, cExternalSource,
RMC/src/Kinetics.h:522:  void InitiateAll(CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry, CDMaterial &cMaterial, CDTally &cTally,
RMC/src/InitiateAll.cpp:13:void CDCriticality::InitiateAll(int p_nParticleMode, CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry,
RMC/src/InitiateAll.cpp:71:  InitiateTrspt(cNeutronTransport, cAceData.p_nDelayNeuFamily);
RMC/src/InitiateAll.cpp:125:void CDFixedSource::InitiateAll(int p_nParticleMode, CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry,
RMC/src/InitiateAll.cpp:154:  InitiateTrspt(cNeutronTransport);
RMC/src/InitiateAll.cpp:211:void CDKinetics::InitiateAll(CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry, CDMaterial &cMaterial,
RMC/src/Criticality.h:89:  InitiateAll(int p_nParticleMode, CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry, CDMaterial &cMaterial,
RMC/src/Criticality.h:755:  void InitiateTrspt(CDNeutronTransport &cNeutronTransport, int nDelayFamilyNum);
RMC/src/ResetCLSCorrection.cpp:11:    InitiateTrspt(cNeutronTransport, cAceData.p_nDelayNeuFamily);
RMC/src/RunCalculation.cpp:6:void CDCalMode::RunCalculation(CDCalMode &cCalMode, CDNeutronTransport cNeutronTransport,
RMC/src/RunCalculation.cpp:86:    CalcFixedSource(cCalMode, cNeutronTransport, cPhotonTransport, cElectronTransport, cAceData,
RMC/src/InitiateTrspt.cpp:7:void CDCriticality::InitiateTrspt(CDNeutronTransport &cNeutronTransport, const int nDelayFamilyNum) {
RMC/src/InitiateTrspt.cpp:60:void CDFixedSource::InitiateTrspt(CDNeutronTransport &cNeutronTransport) {
RMC/src/FixedSource.h:452:  InitiateAll(int p_nParticleMode, CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry, CDMaterial &cMaterial,
RMC/src/FixedSource.h:461:  void InitiateTrspt(CDNeutronTransport &cNeutronTransport);
RMC/src/Sampling.h:216:  * 注意：该函数在RunCalculation中被调用。

## Repeated-run reset candidates
RMC/src/RecordStochasticData.cpp:81:      cTally.p_OCellTallyData.SetZero();
RMC/src/RecordStochasticData.cpp:95:      cTally.p_OSurfTallyData.SetZero();
RMC/src/RecordStochasticData.cpp:109:      cTally.p_OPointTallyData.SetZero();
RMC/src/RecordStochasticData.cpp:124:      cTally.p_OMeshTallyData.SetZero();
RMC/src/RecordStochasticData.cpp:138:      cTally.MaterialTallyData.SetZero();
RMC/src/RecordStochasticData.cpp:153:      cTally.p_OADFCFluxData.SetZero();
RMC/src/RecordStochasticData.cpp:168:      cTally.p_OCsTallyData.SetZero();
RMC/src/InitiatePertPointBurnup.cpp:7:void CDBurnup::InitiatePertBurnup(CDGeometry &cGeometry, CDMaterial &cMaterial, CDTally &cTally, Depth_Class &cDepth,
RMC/src/RestBurnup.cpp:69:  cAceData.ClearData();
RMC/src/RestBurnup.cpp:73:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, *this, cSampling, bPhotonNucleus);
RMC/src/RestBurnup.cpp:113:  cTally.InitiateTally(p_nParticleMode, cGeometry, cAceData, cMaterial, *this,
RMC/src/CalcBurnup.cpp:54:  cBurnup.InitiateBurnup(cGeometry, cMaterial, cTally, BurnDepth, BurnTTA, BurnME);
RMC/src/WriteBinarySrc.cpp:301:      cTally.p_OCellTallyData.SetZero();
RMC/src/WriteBinarySrc.cpp:305:      cTally.p_OMeshTallyData.SetZero();
RMC/src/WriteBinarySrc.cpp:308:      cTally.p_OCsTallyData.SetZero();
RMC/src/WriteBinarySrc.cpp:311:      cTally.p_OPointTallyData.SetZero();
RMC/src/WriteBinarySrc.cpp:314:      cTally.p_OSurfTallyData.SetZero();
RMC/src/SetupCellTallyData.cpp:54:  //// Initiate TallyBuffers
RMC/src/TallyData.cpp:17:void CDTallyData::SetZero() { // expand size of tally data
RMC/src/AdInitialization.cpp:13:    InitiateBurnupSU(cBurnup, cTally, cGeometry, cMaterial, cAceData);
RMC/src/ProcessCycleEnd.cpp:80:  ResetCriticality();
RMC/src/TallyDecomBuffer.cpp:19:  ///// Initiate DecomTallyArray
RMC/src/TallyDecomBuffer.cpp:58:  // Initiate TallyBuffers
RMC/src/CalcKinetics.cpp:9:  cKinetics.InitiateAll(cNeutronTransport, cGeometry, cMaterial, cTally, cAceData, cParticleState, cExternalSource,
RMC/src/InitiateFET.cpp:202:      InitiateLegendre(p_vFETTally[n].p_nLegendreOrder[0], n);   ///因为一维多项式一定是一阶\n
RMC/src/InitiateFET.cpp:204:      InitiateZenike(p_vFETTally[n].p_nZenikeOrder, n);
RMC/src/InitiateFET.cpp:209:      InitiateCylinder(p_vFETTally[n].p_nLegendreOrder[0], p_vFETTally[n].p_nZenikeOrder, n);
RMC/src/InitiateFET.cpp:211:      InitiateDikaer(p_vFETTally[n].p_nLegendreOrder[0], p_vFETTally[n].p_nLegendreOrder[1],
RMC/src/InitiateFET.cpp:217:      InitiateBall(p_vFETTally[n].p_nBallOrder[0], p_vFETTally[n].p_nBallOrder[1], p_vFETTally[n].p_nBallOrder[2], n);
RMC/src/InitiateAndClear.cpp:11:void CDAceData::ClearData() {
RMC/src/Material.h:337:  void InitiateMatAce(int nParticleMode, CDGeometry &cGeometry, CDTally &cTally, CDAceData &cAceData,
RMC/src/ResetTrspt.cpp:8:void CDCriticality::ResetCriticality() {
RMC/src/ResetTrspt.cpp:24://void CDFixedSource::ResetTrspt()
RMC/src/CalcFixedSource.cpp:78:  cFixedSource.InitiateAll(cCalMode.p_nParticleMode, cNeutronTransport, CGeometry, CMaterial, CTally,
RMC/src/FixedSource.h:461:  void InitiateTrspt(CDNeutronTransport &cNeutronTransport);
RMC/src/InitiateMatAce.cpp:8:void CDMaterial::InitiateMatAce(int nParticleMode, CDGeometry &cGeometry, CDTally &cTally, CDAceData &cAceData,
RMC/src/Burnup.h:138:  InitiateBurnup(CDGeometry &cGeometry, CDMaterial &cMaterial, CDTally &cTally, Depth_Class &cDepth,
RMC/src/Burnup.h:917:  void InitiatePertBurnup(CDGeometry &cGeometry, CDMaterial &cMaterial, CDTally &cTally, Depth_Class &cDepth,
RMC/src/Criticality.h:320:  void ResetCriticality();
RMC/src/Criticality.h:755:  void InitiateTrspt(CDNeutronTransport &cNeutronTransport, int nDelayFamilyNum);
RMC/src/Criticality.h:819:  void InitiateXSparameterization(CDTally &cTally, CDMaterial &cMaterial,
RMC/src/Tally.h:89:  void InitiateTally(const int &particleMode, CDGeometry &cGeometry, CDAceData &cAceData, CDMaterial &cMaterial,
RMC/src/Kinetics.h:522:  void InitiateAll(CDNeutronTransport &cNeutronTransport, CDGeometry &cGeometry, CDMaterial &cMaterial, CDTally &cTally,
RMC/src/Adjoint.h:1727:  void InitiateBurnupSU(CDBurnup &cBurnup, CDTally &cTally, CDGeometry &cGeometry, CDMaterial &cMaterial,
RMC/src/AdInitiateBurnupSU.cpp:6:void CDAdjoint::InitiateBurnupSU(CDBurnup &cBurnup, CDTally &cTally, CDGeometry &cGeometry, CDMaterial &cMaterial,
RMC/src/ResetCLSCorrection.cpp:10:    cTally.p_OCellTallyData.SetZero();
RMC/src/ResetCLSCorrection.cpp:11:    InitiateTrspt(cNeutronTransport, cAceData.p_nDelayNeuFamily);
RMC/src/InitiateBurnup.cpp:9:void CDBurnup::InitiateBurnup(CDGeometry &cGeometry, CDMaterial &cMaterial, CDTally &cTally, Depth_Class &cDepth,
RMC/src/InitiateAll.cpp:42:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, cBurnup, cSampling, bPhotonNucleus);
RMC/src/InitiateAll.cpp:71:  InitiateTrspt(cNeutronTransport, cAceData.p_nDelayNeuFamily);
RMC/src/InitiateAll.cpp:88:  InitiateXSparameterization(cTally, cMaterial, cGeometry, cAceData, cBurnup);
RMC/src/InitiateAll.cpp:90:  cTally.InitiateTally(p_nParticleMode, cGeometry, cAceData, cMaterial, cBurnup, p_nNeuNumPerCyc);
RMC/src/InitiateAll.cpp:131:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, cBurnup, cSampling, bPhotonNucleus);
RMC/src/InitiateAll.cpp:154:  InitiateTrspt(cNeutronTransport);
RMC/src/InitiateAll.cpp:156:  cTally.InitiateTally(p_nParticleMode, cGeometry, cAceData, cMaterial, cBurnup, p_llUserInputParNum);
RMC/src/InitiateAll.cpp:216:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, cBurnup, cSampling, bPhotonNucleus);
RMC/src/InitiateAll.cpp:225:  cTally.InitiateTally(p_nParticleMode, cGeometry, cAceData, cMaterial, cBurnup, 0);
RMC/src/AceData.h:147:  void ClearData();
RMC/src/TallyData.h:92:  void SetZero();
RMC/src/InitiateTally.cpp:8:void CDTally::InitiateTally(const int &particleMode, CDGeometry &cGeometry, CDAceData &cAceData, CDMaterial &cMaterial,
RMC/src/InitiateTally.cpp:144:    pTallyData->SetZero();
RMC/src/InitiateTally.cpp:215:    p_OGroupConstantData.SetZero();
RMC/src/InitiateTally.cpp:219:      p_OCollapseGCData.SetZero();
RMC/src/InitiateTally.cpp:224:      p_ONucMicroXS.SetZero();
RMC/src/XSParameterization/InitiateXSParameterization.cpp:6:void CDCriticality::InitiateXSparameterization(CDTally &cTally, CDMaterial &cMaterial, CDGeometry &cGeometry,
RMC/src/CalPertBurnup.cpp:93:      cBurnup.InitiatePertBurnup(cGeometry, cMaterial, cTally, BurnDepth, BurnTTA, BurnME, *this, nNucIndex);
RMC/src/GatherTally.cpp:41:      CTally.p_OSurfTallyData.SetZero();
RMC/src/GatherTally.cpp:55:      CTally.p_OADFCFluxData.SetZero();
RMC/src/GatherTally.cpp:69:      CTally.p_OPointTallyData.SetZero();
RMC/src/GatherTally.cpp:84:      CTally.p_OMeshTallyData.SetZero();
RMC/src/GatherTally.cpp:98:      CTally.MaterialTallyData.SetZero();
RMC/src/GatherTally.cpp:197:      CTally.p_OSurfTallyData.SetZero();
RMC/src/InitiateTrspt.cpp:7:void CDCriticality::InitiateTrspt(CDNeutronTransport &cNeutronTransport, const int nDelayFamilyNum) {
RMC/src/InitiateTrspt.cpp:60:void CDFixedSource::InitiateTrspt(CDNeutronTransport &cNeutronTransport) {

## Mode-sensitive paths
RMC/src/TrackGmaHistory.cpp:131:  if (cParticleState.p_bIsAdjointParticle) {
RMC/src/ProcessMgPhotonCollision.cpp:16:  if (cParticleState.p_bIsAdjointParticle) { //如果是伴随光子，则只考虑散射以及伴随光子产生伴随中子的情形
RMC/src/SampleFreeFlyDist.cpp:85:    if (cParticleState.p_bIsAdjointParticle) { //额外处理伴随总截面
RMC/src/GetExitState.cpp:166:    if (cParticleState.p_bIsAdjointParticle) {
RMC/src/SampleGmaFreeFlyDist.cpp:71:  if (cParticleState.p_bIsAdjointParticle) { //额外处理伴随总截面
RMC/src/InitiateMatAce.cpp:8:void CDMaterial::InitiateMatAce(int nParticleMode, CDGeometry &cGeometry, CDTally &cTally, CDAceData &cAceData,
RMC/src/InitiateMatAce.cpp:65:  if (cAceData.p_bIsMultiGroup && cAceData.p_bIsAdjoint) {
RMC/src/SampleColliType.cpp:157:    if (cParticleState.p_bIsAdjointParticle) { //如果是多群伴随粒子情形
RMC/src/SampleColliType.cpp:318:    if (cParticleState.p_bIsAdjointParticle) { //如果是多群伴随粒子情形
RMC/src/SampleGmaColliNuc.cpp:24:  if (cParticleState.p_bIsAdjointParticle && cAceData.p_bIsMultiGroup) { //deal with adjoint situation
RMC/src/CalcFixedSource.cpp:131:        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
RMC/src/CalcFixedSource.cpp:225:        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
RMC/src/CalcFixedSource.cpp:309:        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
RMC/src/CalcFixedSource.cpp:444:        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
RMC/src/CalcFixedSource.cpp:518:        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
RMC/src/CalcFixedSource.cpp:617:        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
RMC/src/Sampling.h:126:  * 注意：该函数在InitiateMatAce中被调用。
RMC/src/Sampling.h:137:  * 注意：该函数在InitiateMatAce中被调用。
RMC/src/Sampling.h:228:  * 注意：该函数在InitiateMatAce中被调用。
RMC/src/FixedSource.h:270:  bool p_bIsAdjoint = false;
RMC/src/FixedSource.h:475:  void SampleFixSource(CDCalMode &OCalMode, CDNeutronTransport &cNeutronTransport, CDPhotonTransport &cPhotonTransport,
RMC/src/ReadFixedSourceBlock.cpp:228:        if (Paras[0][0] == 1) { cFixedSource.p_bIsAdjoint = true; }
RMC/src/ReadFixedSourceBlock.cpp:234:        } else Output.CheckInputParas( cFixedSource.p_bIsAdjoint,
RMC/src/ProcessNeuGma.cpp:129:    if (cParticleState.p_bIsAdjointParticle) { return; } //伴随计算里面的伴随中子产生伴随光子不在这里进行计算;
RMC/src/SampleColliNuc.cpp:25:  if (cParticleState.p_bIsAdjointParticle && cAceData.p_bIsMultiGroup) { //deal with adjoint situation
RMC/src/InitiateAll.cpp:42:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, cBurnup, cSampling, bPhotonNucleus);
RMC/src/InitiateAll.cpp:130:  if (p_bIsAdjoint) { cAceData.p_bIsAdjoint = true; }
RMC/src/InitiateAll.cpp:131:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, cBurnup, cSampling, bPhotonNucleus);
RMC/src/InitiateAll.cpp:192:  if (p_bIsAdjoint) {
RMC/src/InitiateAll.cpp:216:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, cBurnup, cSampling, bPhotonNucleus);
RMC/src/TreatImpliCapt.cpp:9:  if (cAceData.p_bIsMultiGroup && cParticleState.p_bIsAdjointParticle) { return; }
RMC/src/SampleNeutronSource.cpp:180:void CDFixedSource::SampleFixSource(CDCalMode &OCalMode, CDNeutronTransport &cNeutronTransport,
RMC/src/SampleNeutronSource.cpp:222:  if (cAceData.p_bIsAdjoint) { cParticleState.p_bIsAdjointParticle = true; } //如果使用了固定源伴随计算则粒子是以伴随粒子形式进行输运
RMC/src/SampleNeutronSource.cpp:304:    if (p_bIsAdjoint) {
RMC/src/SampleNeutronSource.cpp:305:      cParticleState.p_bIsAdjointParticle = true;
RMC/src/GetFissionNeuState.cpp:570:  if (cParticleState.p_bIsAdjointParticle) {
RMC/src/GetFissionNeuState.cpp:649:        if (cParticleState.p_bIsAdjointParticle) {
RMC/src/GetFissionNeuState.cpp:726:        if (cParticleState.p_bIsAdjointParticle) {
RMC/src/RestBurnup.cpp:73:  cMaterial.InitiateMatAce(p_nParticleMode, cGeometry, cTally, cAceData, *this, cSampling, bPhotonNucleus);
RMC/src/Material.h:337:  void InitiateMatAce(int nParticleMode, CDGeometry &cGeometry, CDTally &cTally, CDAceData &cAceData,
RMC/src/ParticleState.h:529:  bool p_bIsAdjointParticle = false;
RMC/src/AceData.h:108:    p_bIsAdjoint = false;
RMC/src/AceData.h:1776:  bool p_bIsAdjoint = false;

## HDF5 export
RMC/src/SingleTally.h:652:  void OutputHDF5Mesh(double const *dOriTallyData);
RMC/src/OutputTally.cpp:262:      meshTally.OutputHDF5Mesh(&p_OMeshTallyData.p_vAve[meshTally.p_nDataStartPtr]);
RMC/src/MeshTallyHDF5.cpp:40:void CDMeshTally::OutputHDF5Mesh(double const *dOriTallyData) {
RMC/src/OutputTallyh5.cpp:7:void CDTally::OutputTallyh5(int nMode, int nCyc, int nInActiveCyc, int nDeltaCyc) {
RMC/src/OutputSummary.cpp:187:  CTally.OutputTallyh5(CTally.Final, 0, 0, 0);
RMC/src/Tally.h:210:  void OutputTallyh5(int nMode, int nCyc, int nInActiveCyc, int nDeltaCyc);
RMC/src/ProcessTally.cpp:245:        OutputTallyh5(CritiCyc, cCriticality.p_nCurrentCYCLE, cCriticality.p_nInactCycNum,
RMC/src/ProcessTally.cpp:248:        OutputTallyh5(CritiLastCyc, cCriticality.p_nCurrentCYCLE, cCriticality.p_nInactCycNum,
