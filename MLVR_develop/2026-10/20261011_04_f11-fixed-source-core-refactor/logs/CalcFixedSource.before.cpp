/// @file
/// @copyright Copyright (c) 2000-2026 REAL Tsinghua University. All Rights Reserved.

# include "CalMode.h"
# include "ParallelClass.h"
# include "ElectronTransport.h"
# include "Utility/Timer.h"
# include <ctime>
# include <climits>


bool LoadBalanceTimeChecker(CDFixedSource &cFixedSource, long long particle, time_t *last_t) {
#ifdef USE_MPI
  if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
    return false;
  }

  if (cFixedSource.p_bLoadBalanceReducing) {
    /// 当前进程已经发起了一次非阻塞归约
    int flag = 0;  /// flag=0表示归约尚未完成，flag非0表示归约已经完成
    MPI_Test(&cFixedSource.p_LoadBalanceRequest, &flag, MPI_STATUS_IGNORE);
    if (!flag) {
      /// 若MPI_Iallreduce未完成
      return false;
    }
    /// 若MPI_Iallreduce已经完成
    cFixedSource.p_bLoadBalanceReducing = false;
    cFixedSource.p_LoadBalanceRequest = MPI_REQUEST_NULL;

    if (cFixedSource.p_llLoadBalanceTotal > cFixedSource.p_llUserInputParNum) {
      cFixedSource.p_nFinishCalculate = 5;
      return true;
    }
  }

  /// 当前进程没有发起归约操作，则判断是否达到时间间隔以发起新的归约操作
  time_t current_t = time(nullptr);
  if (current_t - *last_t < cFixedSource.GetLoadBalanceTimeInterval()) {
    /// 未达到时间间隔
    return false;
  }

  *last_t = current_t;
  /// 当前进程已完成的粒子数
  cFixedSource.p_llLoadBalanceSend = particle - 1;
  /// 发起非阻塞全局归约
  MPI_Iallreduce(&cFixedSource.p_llLoadBalanceSend, &cFixedSource.p_llLoadBalanceTotal, 1, MPI_LONG_LONG_INT,
                 MPI_SUM, MPI_COMM_WORLD, &cFixedSource.p_LoadBalanceRequest);

  cFixedSource.p_bLoadBalanceReducing = true;
  return false;
#else
  return false;
#endif
}

void FinalizeLoadBalanceChecker(CDFixedSource &cFixedSource) {
#ifdef USE_MPI
  if (cFixedSource.p_bLoadBalanceReducing) {
    MPI_Wait(&cFixedSource.p_LoadBalanceRequest, MPI_STATUS_IGNORE);
    cFixedSource.p_bLoadBalanceReducing = false;
    cFixedSource.p_LoadBalanceRequest = MPI_REQUEST_NULL;
  }
#endif
}

void CDCalMode::CalcFixedSource(CDCalMode &cCalMode, CDNeutronTransport &cNeutronTransport,
                                CDPhotonTransport &cPhotonTransport, CDElectronTransport &cElectronTransport,
                                CDAceData &CAceData, CDFixedSource &cFixedSource, CDMaterial &CMaterial,
                                CDGeometry &CGeometry, CDParticleState &CParticleState, CDTally &CTally,
                                CDRNG &ORNG, CDCriticality &cCriticality, CDExternalSource cExternalSource,
                                CDSampling &cSampling, CDPerturbation &cPerturb) {
  OTimer.reg(Utility::FixedSource);
  OTimer.reg(Utility::Tally);
  OTimer[Utility::FixedSource].start();
  CDBurnup CBurnup;
  bool bPhotonNucleus = cPhotonTransport.p_bPhotonNucleus;
  cFixedSource.InitiateAll(cCalMode.p_nParticleMode, cNeutronTransport, CGeometry, CMaterial, CTally,
                           CAceData, CParticleState, CBurnup, ORNG, cSampling, bPhotonNucleus,
                           cPhotonTransport, cElectronTransport, cCalMode, cPerturb);
  CParticleState.p_vONucCs.resize(CAceData.p_vNuclides.size());
  CParticleState.p_vIsNucLocCellTmpChanged.resize(CAceData.p_vNuclides.size(), true);

  if (cCalMode.p_nParticleMode == CDCalMode::NeutronPhotonElectronMode ||
      cCalMode.p_nParticleMode == CDCalMode::PhotonElectronMode ||
      cCalMode.p_nParticleMode == CDCalMode::NeutronPhotonMode ||
      cCalMode.p_nParticleMode == CDCalMode::PhotonMode ||
      cCalMode.p_nParticleMode == CDCalMode::ElectronMode) {
    cElectronTransport.GenElectronCross(CAceData, CMaterial);

    OTimer.reg(Utility::PhotonTransport);
    OTimer.reg(Utility::PhotonReaction);
    OTimer.reg(Utility::PhotonXS);
    OTimer.reg(Utility::PhotonTracking);
  }

  time_t last_t = time(nullptr);
  // todo: 1. maybe not compatible with continuous surface source
  //       2. confirmed not compatible with statistics test
  long long TotalCount = 0;
  if (cFixedSource.GetLoadBalanceMethod() == CDFixedSource::TIME_REDUCE) {
    TotalCount = LLONG_MAX;
  }


  if (cCalMode.p_nParticleMode == CDCalMode::NeutronMode) {
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron].push(CDFixBank());
    while (cFixedSource.p_nFinishCalculate < 2) {
      cFixedSource.DistributeSource(CGeometry, cExternalSource, ORNG);
      if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
        TotalCount = cFixedSource.p_llParIntervalEachPro;
      }
      for (long long Neu = 1; Neu <= TotalCount; Neu++) {
        if (LoadBalanceTimeChecker(cFixedSource, Neu, &last_t)) {
          break;
        }

        OTimer[Utility::FixedSource].interval();
        ORNG.GetRandSeed();

        //模拟每个历史前初始化captime变量
        if (CTally.p_bCap) {
          for (auto &cellTally : CTally.p_vCellTally) {
            if (!cellTally.p_vCAPNucZaid.empty()) {
              cellTally.p_vCapTime.clear();
            }
          }
        }

        ///////////////  sample source particle //////////////////////
        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
                                     cExternalSource, CAceData, CMaterial, cSampling, ORNG, Neu);

        //如果自发裂变产生了多个粒子，则将粒子从初始库转移到输运过程的临时中子库中
        if (cExternalSource.p_nFixedInitSrcBankCount > 0) {
          //自发裂变多重性
          for (int i = 0; i < cExternalSource.p_nFixedInitSrcBankCount; ++i) {
            //这里不使用pushinducedparticle函数的原因是没有对应的粒子事件输出;
            cFixedSource.pushInducedParticles(cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron], 1,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dPos,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dDir,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dErg,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dTime,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dWgt);
          }
          cExternalSource.p_nFixedInitSrcBankCount = 0;
          cExternalSource.p_vFixedInitSrcBank.clear();
        }
        CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(0, true);
        if (cFixedSource.p_nFinishCalculate == 2 || cFixedSource.p_nFinishCalculate == 4) {
          break;
        }
        cFixedSource.p_llCurParNumEachPro++;    // 这个变量是当前模拟粒子数，用于判断是否模拟完\n
#ifdef USE_MPI
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + OParallel.p_nProcsNum *
                                           cFixedSource.p_llCurParNumEachPro;
        if (OParallel.p_bIsMaster) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
            printf("neutron : %lld\n", cFixedSource.p_llCurrentPARTICLE);
          }
        }
#else
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + cFixedSource.p_llCurParNumEachPro;
        if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("neutron : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
#endif

        //////////////////  neutron history  /////////////////////////
        for (;;) {
          cFixedSource.TrackHistory(cCalMode, cNeutronTransport, cPhotonTransport, CGeometry, CMaterial, CAceData, CParticleState,
                                    CTally, ORNG, cSampling, cPerturb);
          //清理残余粒子库，这么做的原因是为了保证和WWG功能相适应
          for (int particleType = 1; particleType < 4; particleType++) {
            if (cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
              while (cFixedSource.p_vFixedParticleSrcBank[particleType].top().calculateTime == 0
                     && cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
                cFixedSource.p_vFixedParticleSrcBank[particleType].pop();
              }
            }
          }
          if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Neutron, ORNG);
          } else {
            break;
          }
        }

        //模拟完一个历史后对当前历史进行cap数据处理
        if (CTally.p_bCap) {
          CTally.ProcessCapData();
        }

        //模拟完一个历史后对当前历史微扰系数进行处理
        if (cPerturb.p_bDiffrOprt) {
          cPerturb.ProcessFixedSrcPerb();
        }

        CParticleState.p_dSimulateTime = OTimer[Utility::FixedSource].interval();
#ifdef USE_MPI
        CTally.SumUpTally(Neu + cFixedSource.p_llParticlePosEachPro,
                          CParticleState.p_dSimulateTime);   // fixed-source calculations
#else
        CTally.SumUpTally(Neu, CParticleState.p_dSimulateTime);
#endif
        // todo: handling this.
//        if (cFixedSource.p_nFinishCalculate != -1) { break; }
      }
      cFixedSource.PrcoessBatchEnd(CTally, cNeutronTransport, CGeometry, CMaterial, CAceData,
                                   cExternalSource, cCalMode, ORNG);
    }
  } else if (cCalMode.p_nParticleMode == CDCalMode::PhotonMode) {
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].push(CDFixBank());
    while (cFixedSource.p_nFinishCalculate < 2) {
      cFixedSource.DistributeSource(CGeometry, cExternalSource, ORNG);
      if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
        TotalCount = cFixedSource.p_llParIntervalEachPro;
      }
      for (long long Pho = 1; Pho <= TotalCount; Pho++) {
        if (LoadBalanceTimeChecker(cFixedSource, Pho, &last_t)) {
          break;
        }

        OTimer[Utility::FixedSource].interval();
        ORNG.GetRandSeed();
        ///////////////  sample source particle //////////////////////
        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
                                     cExternalSource, CAceData, CMaterial, cSampling, ORNG, Pho);
        Output.CheckInputParas( CParticleState.p_eParticleType == CDParticleState::Photon,
        [&]() {sprintf(Output.p_sPrintStr, "illegal particle type( photon particle source needed in this MODE ) in source card in EXTERNSOUREC block in Photon Calculation Mode.\n");},
        CDOutput::_ERROR);
        if (cFixedSource.p_nFinishCalculate == 2 || cFixedSource.p_nFinishCalculate == 4) {
          break;
        }
        CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, true);
        cFixedSource.p_llCurParNumEachPro++;    // 这个变量是当前模拟粒子数，用于判断是否模拟完\n
# ifdef USE_MPI
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + OParallel.p_nProcsNum *
                                           cFixedSource.p_llCurParNumEachPro;
        if (OParallel.p_bIsMaster) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
            printf("photon : %lld\n", cFixedSource.p_llCurrentPARTICLE);
          }
        }
# else
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + cFixedSource.p_llCurParNumEachPro;
        if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("photon : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
# endif
        //////////////////  photon history  /////////////////////////
        for (;;) {
          if (CParticleState.p_eParticleType == CDParticleState::Photon) {
            cPhotonTransport.TrackGmaHistory(cCalMode, cFixedSource, cCriticality, CGeometry, CMaterial,
                                             CAceData, CParticleState, CTally, ORNG, cElectronTransport,
                                             cSampling);
          } else if (CParticleState.p_eParticleType == CDParticleState::Electron ||
                     CParticleState.p_eParticleType == CDParticleState::Positron) {
            cElectronTransport.TrackElectronHistory(cCalMode, cFixedSource, cCriticality, CGeometry,
                                                    CMaterial, CAceData, ORNG, CParticleState, CTally,
                                                    cPhotonTransport, cSampling);
          }
          //清理残余粒子库，这么做的原因是为了保证和WWG功能相适应
          for (int particleType = 1; particleType < 4; particleType++) {
            if (cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
              while (cFixedSource.p_vFixedParticleSrcBank[particleType].top().calculateTime == 0
                     && cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
                cFixedSource.p_vFixedParticleSrcBank[particleType].pop();
              }
            }
          }
          if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Photon, ORNG);
            CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, false);
          }  else if (cFixedSource.p_nElectronBankCount > 0) {
            cFixedSource.SamplElectronBank(CGeometry, CParticleState, ORNG);
            CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(static_cast<int>(CParticleState.p_eParticleType) - 1,
                false);
          } else {
            break;
          }
        }
        CParticleState.p_dSimulateTime = OTimer[Utility::FixedSource].interval();
#ifdef USE_MPI
        CTally.SumUpTally(Pho + cFixedSource.p_llParticlePosEachPro,
                          CParticleState.p_dSimulateTime);   // fixed-source calculations
#else
        CTally.SumUpTally(Pho, CParticleState.p_dSimulateTime);
#endif
        if (cFixedSource.p_nFinishCalculate != -1) {
          break;
        }
      }
      cFixedSource.PrcoessBatchEnd(CTally, cNeutronTransport, CGeometry, CMaterial, CAceData, cExternalSource, cCalMode,
                                   ORNG);
    }
  } else if (cCalMode.p_nParticleMode == CDCalMode::NeutronPhotonMode) {
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron].push(CDFixBank());
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].push(CDFixBank());
    while (cFixedSource.p_nFinishCalculate < 2) {
      cFixedSource.DistributeSource(CGeometry, cExternalSource, ORNG);
      if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
        TotalCount = cFixedSource.p_llParIntervalEachPro;
      }
      for (long long Particle = 1; Particle <= TotalCount; Particle++) {
        if (LoadBalanceTimeChecker(cFixedSource, Particle, &last_t)) {
          break;
        }

        OTimer[Utility::FixedSource].interval();
        ORNG.GetRandSeed();
        ///////////////  sample source particle //////////////////////
        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
                                     cExternalSource,
                                     CAceData, CMaterial, cSampling,
                                     ORNG, Particle);
        if (cExternalSource.p_nFixedInitSrcBankCount > 0) {
          //自发裂变多重性
          for (int i = 0; i < cExternalSource.p_nFixedInitSrcBankCount; ++i) {
            //这里不使用pushinducedparticle函数的原因是没有对应的粒子事件输出;
            cFixedSource.pushInducedParticles(cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron], 1,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dPos,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dDir,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dErg,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dTime,
                                              cExternalSource.p_vFixedInitSrcBank[i].p_dWgt);
          }
          cExternalSource.p_nFixedInitSrcBankCount = 0;
          cExternalSource.p_vFixedInitSrcBank.clear();
        }
        if (cExternalSource.p_nFixedInitPhoSrcBankCount > 0) {
          //自发裂变多重性
          for (int i = 0; i < cExternalSource.p_nFixedInitPhoSrcBankCount; ++i) {
            //这里不使用pushinducedparticle函数的原因是没有对应的粒子事件输出;
            cFixedSource.pushInducedParticles(cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon], 1,
                                              cExternalSource.p_vFixedInitPhoSrcBank[i].p_dPos,
                                              cExternalSource.p_vFixedInitPhoSrcBank[i].p_dDir,
                                              cExternalSource.p_vFixedInitPhoSrcBank[i].p_dErg,
                                              cExternalSource.p_vFixedInitPhoSrcBank[i].p_dTime,
                                              cExternalSource.p_vFixedInitPhoSrcBank[i].p_dWgt);
          }
          cExternalSource.p_nFixedInitPhoSrcBankCount = 0;
          cExternalSource.p_vFixedInitPhoSrcBank.clear();
        }
        if (cFixedSource.p_nFinishCalculate == 2 || cFixedSource.p_nFinishCalculate == 4) {
          break;
        }
        cFixedSource.p_llCurParNumEachPro++;    // 这个变量是当前模拟粒子数，用于判断是否模拟完\n
        if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(0, true);
        } else if (CParticleState.p_eParticleType == CDParticleState::Photon) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, true);
        }

# ifdef USE_MPI
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + OParallel.p_nProcsNum *
                                           cFixedSource.p_llCurParNumEachPro;
        if (OParallel.p_bIsMaster) {
          if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("neutron : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          } else {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("photon : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          }
        }
# else
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + cFixedSource.p_llCurParNumEachPro;
        if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("neutron : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        } else {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("photon : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        }
# endif

        //////////////////  neutron history  /////////////////////////
        for (;;) {
          if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
            cFixedSource.TrackHistory(cCalMode, cNeutronTransport, cPhotonTransport, CGeometry,
                                      CMaterial, CAceData, CParticleState, CTally, ORNG, cSampling,
                                      cPerturb);
          } else if (CParticleState.p_eParticleType == CDParticleState::Photon) {
            cPhotonTransport.TrackGmaHistory(cCalMode, cFixedSource, cCriticality, CGeometry, CMaterial, CAceData,
                                             CParticleState, CTally, ORNG, cElectronTransport, cSampling);
          } else if (CParticleState.p_eParticleType == CDParticleState::Electron ||
                     CParticleState.p_eParticleType == CDParticleState::Positron) {
            cElectronTransport.TrackElectronHistory(cCalMode, cFixedSource,
                                                    cCriticality, CGeometry, CMaterial, CAceData,
                                                    ORNG, CParticleState, CTally, cPhotonTransport, cSampling);
          } else {
            Output.OutputMessage([&]()
            { sprintf(Output.p_sPrintStr, "Undefined particle type!.\n"); },
            Output.p_fpOutputFilePtr, CDOutput::_ERROR);
          }
          //清理残余粒子库，这么做的原因是为了保证和WWG功能相适应
          for (int particleType = 1; particleType < 4; particleType++) {
            if (cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
              while (cFixedSource.p_vFixedParticleSrcBank[particleType].top().calculateTime == 0
                     && cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
                cFixedSource.p_vFixedParticleSrcBank[particleType].pop();
              }
            }
          }
          if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Neutron, ORNG);
            CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(0, false);
          } else if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Photon, ORNG);
            CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, false);
          } else if (cFixedSource.p_nElectronBankCount > 0) {
            cFixedSource.SamplElectronBank(CGeometry, CParticleState, ORNG);
            CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(static_cast<int>(CParticleState.p_eParticleType) - 1,
                false);
          } else {
            break;
          }
        }
        CParticleState.p_dSimulateTime = OTimer[Utility::FixedSource].interval();
#ifdef USE_MPI
        CTally.SumUpTally(Particle + cFixedSource.p_llParticlePosEachPro,
                          CParticleState.p_dSimulateTime);   // fixed-source calculations
#else
        CTally.SumUpTally(Particle, CParticleState.p_dSimulateTime);
#endif
        if (cFixedSource.p_nFinishCalculate != -1) {
          break;
        }
      }
      cFixedSource.PrcoessBatchEnd(CTally, cNeutronTransport, CGeometry, CMaterial, CAceData, cExternalSource, cCalMode,
                                   ORNG);
    }
  } else if (cCalMode.p_nParticleMode == CDCalMode::ElectronMode) {
    while (cFixedSource.p_nFinishCalculate < 2) {
      cFixedSource.DistributeSource(CGeometry, cExternalSource, ORNG);
      if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
        TotalCount = cFixedSource.p_llParIntervalEachPro;
      }
      for (long long nElectron = 1; nElectron <= TotalCount; nElectron++) {
        if (LoadBalanceTimeChecker(cFixedSource, nElectron, &last_t)) {
          break;
        }

        OTimer[Utility::FixedSource].interval();
        ORNG.GetRandSeed();
        ///////////////  sample source particle //////////////////////
        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
                                     cExternalSource,
                                     CAceData, CMaterial, cSampling,
                                     ORNG, nElectron);
        Output.CheckInputParas( CParticleState.p_eParticleType == CDParticleState::Electron,
        [&]() {sprintf(Output.p_sPrintStr, "illegal particle type( photon particle source needed in this MODE ) in source card in EXTERNSOUREC block in Photon Calculation Mode.\n");},
        CDOutput::_ERROR);
        if (cFixedSource.p_nFinishCalculate == 2 || cFixedSource.p_nFinishCalculate == 4) {
          break;
        }
        CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, true);
        cFixedSource.p_llCurParNumEachPro++;    // 这个变量是当前模拟粒子数，用于判断是否模拟完\n
# ifdef USE_MPI
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + OParallel.p_nProcsNum *
                                           cFixedSource.p_llCurParNumEachPro;
        if (OParallel.p_bIsMaster) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
            printf("electron : %lld\n", cFixedSource.p_llCurrentPARTICLE);
          }
        }
# else
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + cFixedSource.p_llCurParNumEachPro;
        if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("electron : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
# endif

        //////////////////  neutron history  /////////////////////////
        for (;;) {
          cElectronTransport.TrackElectronHistory(cCalMode, cFixedSource,
                                                  cCriticality, CGeometry, CMaterial, CAceData,
                                                  ORNG, CParticleState, CTally, cPhotonTransport, cSampling);
          //清理残余粒子库，这么做的原因是为了保证和WWG功能相适应
          for (int particleType = 1; particleType < 4; particleType++) {
            if (cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
              while (cFixedSource.p_vFixedParticleSrcBank[particleType].top().calculateTime == 0
                     && cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
                cFixedSource.p_vFixedParticleSrcBank[particleType].pop();
              }
            }
          }
          if (cFixedSource.p_nElectronBankCount > 0) {
            cFixedSource.SamplElectronBank(CGeometry, CParticleState, ORNG);
          } else {
            break;
          }
        }
        CParticleState.p_dSimulateTime = OTimer[Utility::FixedSource].interval();
#ifdef USE_MPI
        CTally.SumUpTally(nElectron + cFixedSource.p_llParticlePosEachPro,
                          CParticleState.p_dSimulateTime);   // fixed-source calculations
#else
        CTally.SumUpTally(nElectron, CParticleState.p_dSimulateTime);
#endif
        if (cFixedSource.p_nFinishCalculate != -1) {
          break;
        }
      }
      cFixedSource.PrcoessBatchEnd(CTally, cNeutronTransport, CGeometry, CMaterial, CAceData, cExternalSource, cCalMode,
                                   ORNG);
    }
  } else if (cCalMode.p_nParticleMode == CDCalMode::PhotonElectronMode) {
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].push(CDFixBank());
    while (cFixedSource.p_nFinishCalculate < 2) {
      cFixedSource.DistributeSource(CGeometry, cExternalSource, ORNG);
      if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
        TotalCount = cFixedSource.p_llParIntervalEachPro;
      }
      for (long long Particle = 1; Particle <= TotalCount; Particle++) {
        if (LoadBalanceTimeChecker(cFixedSource, Particle, &last_t)) {
          break;
        }

        OTimer[Utility::FixedSource].interval();
        ORNG.GetRandSeed();
        ///////////////  sample source particle //////////////////////
        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
                                     cExternalSource,
                                     CAceData, CMaterial, cSampling,
                                     ORNG, Particle);
        if (cFixedSource.p_nFinishCalculate == 2 || cFixedSource.p_nFinishCalculate == 4) {
          break;
        }
        cFixedSource.p_llCurParNumEachPro++;    // 这个变量是当前模拟粒子数，用于判断是否模拟完\n
        if (CParticleState.p_eParticleType == CDParticleState::Photon) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(0, true);
        } else if (CParticleState.p_eParticleType == CDParticleState::Electron) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, true);
        }

# ifdef USE_MPI
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + OParallel.p_nProcsNum *
                                           cFixedSource.p_llCurParNumEachPro;
        if (OParallel.p_bIsMaster) {
          if (CParticleState.p_eParticleType == CDParticleState::Photon) {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("photon : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          } else if (CParticleState.p_eParticleType == CDParticleState::Electron) {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("electron : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          }
        }
# else
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + cFixedSource.p_llCurParNumEachPro;
        if (CParticleState.p_eParticleType == CDParticleState::Photon) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("Photon : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        } else if (CParticleState.p_eParticleType == CDParticleState::Electron) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("electron : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        }
# endif

        //////////////////  Photon history  /////////////////////////
        for (;;) {
          if (CParticleState.p_eParticleType == CDParticleState::Photon) {
            cPhotonTransport.TrackGmaHistory(cCalMode, cFixedSource, cCriticality, CGeometry, CMaterial, CAceData,
                                             CParticleState, CTally, ORNG, cElectronTransport, cSampling);
          } else if (CParticleState.p_eParticleType == CDParticleState::Electron ||
                     CParticleState.p_eParticleType == CDParticleState::Positron) {
            cElectronTransport.TrackElectronHistory(cCalMode, cFixedSource,
                                                    cCriticality, CGeometry, CMaterial, CAceData,
                                                    ORNG, CParticleState, CTally, cPhotonTransport, cSampling);
          } else {
            Output.OutputMessage([&]()
            { sprintf(Output.p_sPrintStr, "Undefined particle type!.\n"); },
            Output.p_fpOutputFilePtr, CDOutput::_ERROR);
          }
          //清理残余粒子库，这么做的原因是为了保证和WWG功能相适应
          for (int particleType = 1; particleType < 4; particleType++) {
            if (cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
              while (cFixedSource.p_vFixedParticleSrcBank[particleType].top().calculateTime == 0
                     && cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
                cFixedSource.p_vFixedParticleSrcBank[particleType].pop();
              }
            }
          }
          if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Photon, ORNG);
          } else if (cFixedSource.p_nElectronBankCount > 0) {
            cFixedSource.SamplElectronBank(CGeometry, CParticleState, ORNG);
          } else {
            break;
          }
        }
        CParticleState.p_dSimulateTime = OTimer[Utility::FixedSource].interval();
#ifdef USE_MPI
        CTally.SumUpTally(Particle + cFixedSource.p_llParticlePosEachPro,
                          CParticleState.p_dSimulateTime);   // fixed-source calculations
#else
        CTally.SumUpTally(Particle, CParticleState.p_dSimulateTime);
#endif
        if (cFixedSource.p_nFinishCalculate != -1) {
          break;
        }
      }
      cFixedSource.PrcoessBatchEnd(CTally, cNeutronTransport, CGeometry, CMaterial, CAceData, cExternalSource, cCalMode,
                                   ORNG);
    }
  } else if (cCalMode.p_nParticleMode == CDCalMode::NeutronPhotonElectronMode) {
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron].push(CDFixBank());
    cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].push(CDFixBank());
    while (cFixedSource.p_nFinishCalculate < 2) {
      cFixedSource.DistributeSource(CGeometry, cExternalSource, ORNG);
      if (cFixedSource.GetLoadBalanceMethod() != CDFixedSource::TIME_REDUCE) {
        TotalCount = cFixedSource.p_llParIntervalEachPro;
      }
      for (long long Particle = 1; Particle <= TotalCount; Particle++) {
        if (LoadBalanceTimeChecker(cFixedSource, Particle, &last_t)) {
          break;
        }

        OTimer[Utility::FixedSource].interval();
        ORNG.GetRandSeed();
        ///////////////  sample source particle //////////////////////
        cFixedSource.SampleFixSource(*this, cNeutronTransport, cPhotonTransport, CGeometry, CParticleState,
                                     cExternalSource,
                                     CAceData, CMaterial, cSampling,
                                     ORNG, Particle);
        if (cFixedSource.p_nFinishCalculate == 2 || cFixedSource.p_nFinishCalculate == 4) {
          break;
        }
        cFixedSource.p_llCurParNumEachPro++;    // 这个变量是当前模拟粒子数，用于判断是否模拟完\n
        if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(0, true);
        } else if (CParticleState.p_eParticleType == CDParticleState::Photon) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(1, true);
        } else if (CParticleState.p_eParticleType == CDParticleState::Electron) {
          CGeometry.p_OBinaryOut.UpdateParticleTypeAndHistoryNum(2, true);
        }

# ifdef USE_MPI
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + OParallel.p_nProcsNum *
                                           cFixedSource.p_llCurParNumEachPro;
        if (OParallel.p_bIsMaster) {
          if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("Neutron : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          } else if (CParticleState.p_eParticleType == CDParticleState::Photon) {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("Photon : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          } else if (CParticleState.p_eParticleType == CDParticleState::Electron) {
            if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) {
              printf("Electron : %lld\n", cFixedSource.p_llCurrentPARTICLE);
            }
          }
        }
# else
        cFixedSource.p_llCurrentPARTICLE = cFixedSource.p_llParNumRestart + cFixedSource.p_llCurParNumEachPro;
        if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("Neutron : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        } else if (CParticleState.p_eParticleType == CDParticleState::Photon) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("Photon : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        } else if (CParticleState.p_eParticleType == CDParticleState::Electron) {
          if (cFixedSource.p_llCurParNumEachPro % 1000 == 0) { printf("Electron : %lld\n", cFixedSource.p_llCurrentPARTICLE); }
        }
# endif

        //////////////////  neutron history  /////////////////////////
        for (;;) {
          if (CParticleState.p_eParticleType == CDParticleState::Neutron) {
            cFixedSource.TrackHistory(cCalMode, cNeutronTransport, cPhotonTransport, CGeometry,
                                      CMaterial, CAceData, CParticleState, CTally, ORNG, cSampling,
                                      cPerturb);
          } else if (CParticleState.p_eParticleType == CDParticleState::Photon) {
            cPhotonTransport.TrackGmaHistory(cCalMode, cFixedSource, cCriticality, CGeometry, CMaterial,
                                             CAceData, CParticleState, CTally, ORNG, cElectronTransport,
                                             cSampling);
          } else if (CParticleState.p_eParticleType == CDParticleState::Electron ||
                     CParticleState.p_eParticleType == CDParticleState::Positron) {
            cElectronTransport.TrackElectronHistory(cCalMode, cFixedSource, cCriticality, CGeometry,
                                                    CMaterial, CAceData, ORNG, CParticleState, CTally,
                                                    cPhotonTransport, cSampling);
          } else {
            Output.OutputMessage([&]()
            { sprintf(Output.p_sPrintStr, "Undefined particle type!.\n"); },
            Output.p_fpOutputFilePtr, CDOutput::_ERROR);
          }
          //清理残余粒子库，这么做的原因是为了保证和WWG功能相适应
          for (int particleType = 1; particleType < 4; particleType++) {
            if (cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
              while (cFixedSource.p_vFixedParticleSrcBank[particleType].top().calculateTime == 0
                     && cFixedSource.p_vFixedParticleSrcBank[particleType].size() > 1) {
                cFixedSource.p_vFixedParticleSrcBank[particleType].pop();
              }
            }
          }
          if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Neutron].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Neutron, ORNG);
          }
          if (cFixedSource.p_vFixedParticleSrcBank[CDParticleState::Photon].size() > 1) {
            cFixedSource.SampleFromParticleBank(CGeometry, CParticleState, CDParticleState::Photon, ORNG);
          } else if (cFixedSource.p_nElectronBankCount > 0) {
            cFixedSource.SamplElectronBank(CGeometry, CParticleState, ORNG);
          } else {
            break;
          }
        }
        CParticleState.p_dSimulateTime = OTimer[Utility::FixedSource].interval();
#ifdef USE_MPI
        CTally.SumUpTally(Particle + cFixedSource.p_llParticlePosEachPro,
                          CParticleState.p_dSimulateTime);   // fixed-source calculations
#else
        CTally.SumUpTally(Particle, CParticleState.p_dSimulateTime);

#endif
        if (cFixedSource.p_nFinishCalculate != -1) {
          break;
        }
      }
      cFixedSource.PrcoessBatchEnd(CTally, cNeutronTransport, CGeometry, CMaterial, CAceData, cExternalSource, cCalMode,
                                   ORNG);
    }
  }

  FinalizeLoadBalanceChecker(cFixedSource);

  CTally.ProcessTally(cFixedSource, CMaterial, CAceData);

  if (cPerturb.p_bDiffrOprt) {
    cPerturb.CalcFixedSrcPerbCoeffs(cFixedSource.p_llUserInputParNum);
    cPerturb.OutputFixSrcPerbCoeffs();
  }

  if (OWeightWindow.p_bWeightWindowGeneratorOn) {
#ifdef USE_MPI
    OWeightWindow.GatherTotalWeight();
#endif
    OWeightWindow.CalculateWeightWindow();
    OWeightWindow.OutputWWOUTFile(CGeometry, cCalMode.p_nParticleMode);
  }
#ifdef USE_MPI
  MPI_Barrier(MPI_COMM_WORLD);
  if (OWeightWindow.p_bUseSharedMPIWeightWindow) {
    MPI_Win_free(&OWeightWindow.WeightWindowParaDataShareWindow);
  }
#endif
  Output.OutputWrtSurfSrc(CGeometry);
  Output.OutputSummary(cCalMode, cNeutronTransport, cFixedSource, CTally, CMaterial);
# ifdef USE_PYTHON_API
  //如果使用了外源子程序，则在此关闭python解释器
  if (OPythonInterface.p_bSourceSub) {
    OPythonInterface.FinalizePython();
  }
# endif
  OTimer[Utility::FixedSource].stop();
}
