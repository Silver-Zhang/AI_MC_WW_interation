  // Task-private experiment main. Original neutron history loop remains in CalcFixedSource.
  const char* seq_path=std::getenv("F11_SEQUENCE");
  f11_probe::require(seq_path!=nullptr,"F11_SEQUENCE is required for test driver");
  std::ifstream seq(seq_path);
  std::string rid; long long n; unsigned long long seed; int adj,ww_id; double source_x;
  size_t ordinal=0;
  while(seq>>rid>>n>>seed>>adj>>source_x>>ww_id) {
    f11_probe::set_run(rid);
    f11_probe::bind_model(OGeometry,OMaterial);
    if(ordinal==0) {
      f11_probe::require(OFixedSource.p_llUserInputParNum==n && ORNG.GetSeed0()==seed && OFixedSource.p_bIsAdjoint==bool(adj),"first input disagrees with sequence");
      f11_probe::require(OExternalSource.p_vSource.size()==1 && OExternalSource.p_vSource[0].p_vPoints.at(0)==source_x,"first source disagrees with sequence");
    } else {
#ifdef RMC_F11_REUSE_EXPERIMENT
      // Previous files were closed by original OutputEnding. Clear dangling FILE* only.
      Output.p_fpOutputFilePtr=nullptr;Output.p_fpTallyFilePtr=nullptr;Output.p_fpMatFilePtr=nullptr;
      Output.p_fpCycTallyFilePtr=nullptr;Output.p_fpFissMutiInfoFilePtr=nullptr;
      delete Output.p_Result;delete Output.p_Infomation;delete Output.p_State;
      Output.p_Result=nullptr;Output.p_Infomation=nullptr;Output.p_State=nullptr;
      Output.p_nWarningCount=0;Output.p_nErrorCount=0;
      OTimer=Utility::RMCTimer();
      std::string input="inp_"+rid,output=input+".out", data=std::getenv("RMC_DATA_PATH");
      std::vector<std::string>args={"F11Driver","-i",input,"-o",output,"-d",data};
      std::vector<char*>argv2;for(auto&v:args)argv2.push_back(&v[0]);
      OInput.CheckIOFile(argv2.size(),argv2.data());
      Output.OutputHeading(OCriticality);
      std::map<std::string,bool>blocks;blocks["MATERIAL"]=true;blocks["TALLY"]=true;
      Output.OpenFilePtrs(blocks,OCalMode);
      f11_probe::snapshot("before_clear",OFixedSource,OAceData,OParticleState,OTally,ORNG,OExternalSource);
      // CLEAR calculation progress and history banks; SET population and intervals.
      OFixedSource.p_nFinishCalculate=-1;
      OFixedSource.p_llCurParNumEachPro=0;OFixedSource.p_llCurTotParNum=0;
      OFixedSource.p_llCurrentBatch=0;OFixedSource.p_llCurrentPARTICLE=0;
      OFixedSource.p_llParNumRestart=0;OFixedSource.p_llParticlePosEachPro=0;OFixedSource.p_llParIntervalEachPro=0;
      OFixedSource.p_llUserInputParNum=n;OFixedSource.CheckFixedSource();
      OFixedSource.p_dTotStartWgt=0;OFixedSource.p_dTotStartWgtOrigin=0;
      OFixedSource.p_nFixedSrcCount=0;OFixedSource.p_nFixedSrcBankCount=0;
      OFixedSource.p_nPhotonBankCount=0;OFixedSource.p_nElectronBankCount=0;OFixedSource.p_nMissParCount=0;
      OFixedSource.p_llTotCollisionCount=0;OFixedSource.p_llTotGammaColliCount=0;OFixedSource.p_llTotElectronColliCount=0;OFixedSource.p_dTotInducedGammaCount=0;
      for(auto&bank:OFixedSource.p_vFixedParticleSrcBank)bank.ParticleBank.clear();
      OFixedSource.p_vFixedSrc.clear();OFixedSource.p_vFixedSrcBank.clear();OFixedSource.p_vPhotonBank.clear();OFixedSource.p_vElectronBank.clear();
      for(auto*v:{&OFixedSource.p_vSpontaFissNeuMul,&OFixedSource.p_vInduceFissNeuMul,&OFixedSource.p_vSpontaFissPhoMul,&OFixedSource.p_vInduceFissPhoMul})std::fill(v->begin(),v->end(),0);
      std::fill(OFixedSource.p_sNextParticle.begin(),OFixedSource.p_sNextParticle.end(),0);
      ONeutronTransport.p_nMissParticleCount=0;ONeutronTransport.p_nMissNeutronCount=0;
      OExternalSource.p_vFixedInitSrcBank.clear();OExternalSource.p_vFixedInitPhoSrcBank.clear();
      OExternalSource.p_nFixedInitSrcBankCount=0;OExternalSource.p_nFixedInitPhoSrcBankCount=0;
      std::fill(OExternalSource.p_vSpontaFissNeuMul.begin(),OExternalSource.p_vSpontaFissNeuMul.end(),0);
      std::fill(OExternalSource.p_vSpontaFissPhoMul.begin(),OExternalSource.p_vSpontaFissPhoMul.end(),0);
      OExternalSource.p_vSource[0].p_vPoints={source_x,0,0};
      ORNG.ResetRNGType(CDRNG::rngLCG63_0);ORNG.SetSeed0(seed);ORNG.SetStride(1000000);ORNG.SetPosition(0);ORNG.SetPositionPre(-1000);
      // KEEP tally owner, definitions, registry and statistical index; CLEAR run samples.
      for(auto*d:OTally.p_pTallyDataPointer){
        d->SetZero();std::fill(d->p_vSum3.begin(),d->p_vSum3.end(),0);
        d->p_setScoreIndex.clear();d->p_vScoreIndex2.clear();d->p_vScoreStride.clear();
        d->p_OStatisticsTester.p_vGatherScores.clear();
        if(OTally.p_bUseStatisticsCheck) d->p_OStatisticsTester.ReSize(n);
      }
      f11_probe::snapshot("after_clear",OFixedSource,OAceData,OParticleState,OTally,ORNG,OExternalSource);
      // REBUILD mode-derived arrays from the retained raw MGACE base.
      OFixedSource.p_bIsAdjoint=bool(adj);OAceData.p_bIsAdjoint=bool(adj);
      for(size_t k=1;k<OAceData.p_vNuclides.size();++k){
        OAceData.p_vNuclides[k].p_vAdjointCrossSection.clear();
        OAceData.p_vNuclides[k].p_vAdjointFissionCrossSection.clear();
      }
      f11_probe::snapshot("mode_zero_base",OFixedSource,OAceData,OParticleState,OTally,ORNG,OExternalSource);
      if(adj) OAceData.treatAdjointMaterial(OCalMode.p_nParticleMode);
      OFixedSource.p_dMaxAdjointNeutronEnergy=adj?OAceData.LocateMgErgGrp(30,CDParticleState::Neutron):20;
      OFixedSource.p_dMaxAdjointPhotonEnergy=adj?30:20;
      // Destroy/reconstruct per-particle scratch state in place; no geometry/material/tally copy.
      OParticleState.~CDParticleState();new(&OParticleState) CDParticleState();
      OParticleState.p_bIsAdjointParticle=bool(adj);
      OParticleState.energyCutoff(CDParticleState::Neutron)=ONeutronTransport.p_dEg0CutOff;
      OParticleState.energyCutoff(CDParticleState::Photon)=OPhotonTransport.p_dErgCutGma;
      OParticleState.energyCutoff(CDParticleState::Electron)=0;OParticleState.energyCutoff(CDParticleState::Positron)=0;
      OParticleState.p_vNearestParticleID.resize(OGeometry.p_vUniverse.size());
      OParticleState.p_vNearestPoissonBoxID.resize(OGeometry.p_vUniverse.size());
      OParticleState.p_dRealDisplace.resize(OGeometry.p_vUniverse.size()+1,std::vector<double>(3));
      OMaterial.SetupMatNucFrc(OParticleState);
      OParticleState.p_vONucCs.resize(OAceData.p_vNuclides.size());
      OParticleState.p_vIsNucLocCellTmpChanged.resize(OAceData.p_vNuclides.size(),true);
      OFixedSource.InitiateTrspt(ONeutronTransport);
      OTally.p_bIsPerHstry=true;OTally.p_bIsPerCyc=false;
      // SET only numerical lower bounds; REBUILD upper/survival through the original function.
      std::vector<double>lower;for(int i=0;i<2;++i)for(int g=0;g<30;++g)lower.push_back(std::ldexp(1.,-1-i-(g%2))/(ww_id==2?4:1));
      OWeightWindow.ProcessWeightWindow(OGeometry,1,OWeightWindow.p_vEnergyBins[1],lower,5,3);
      f11_probe::snapshot("after_rebuild_before_arm",OFixedSource,OAceData,OParticleState,OTally,ORNG,OExternalSource);
      f11_probe::arm(OFixedSource,OAceData,OParticleState,OTally,ORNG,OExternalSource);
#else
      f11_probe::require(false,"uninstrumented driver supports fresh mode only");
#endif
    }
    OSampling.InitialBeforeCalculation(OBurnup,ORNG);
    F11DriverAccess::run(OCalMode,OCalMode,ONeutronTransport,OPhotonTransport,OElectronTransport,OAceData,
          OFixedSource,OMaterial,OGeometry,OParticleState,OTally,ORNG,OCriticality,OExternalSource,OSampling,OPerturb);
    // This endpoint read also exists in the P0-disabled fresh driver, after the production call.
    f11_probe::snapshot("driver_after_return",OFixedSource,OAceData,OParticleState,OTally,ORNG,OExternalSource);
    Output.OutputEnding(OCalMode,OAdjoint,OCriticality,OFixedSource);
    f11_probe::flush();
    ++ordinal;
  }
  f11_probe::require(ordinal>0,"empty sequence manifest");
  return 0;
}
