/// @file
/// @copyright Copyright (c) 2000-2026 REAL Tsinghua University. All Rights Reserved.
/// @brief 计算模式头文件

# ifndef __CALMODE__H__
# define  __CALMODE__H__

# include "Criticality.h"
# include "Tally.h"
# include "AceData.h"
# include "Geometry.h"
# include "Material.h"
# include "Burnup.h"
# include "Output.h"
# include "Plot.h"
# include "Convergence.h"
# include "Depth_Class.h"
# include "FixedSource.h"
# include "Adjoint.h"
# include "ExternalSource.h"
# include "PhotonTransport.h"
# include "ElectronTransport.h"
# include "Adjoint.h"
# include "Sampling.h"
# include "WeightWindow.h"
# include "Kinetics.h"

using namespace std;

class CDExternalSource;

class CDPhotonTransport;
class CDKinetics;

/**
 * @brief 计算模式类
 */
class CDCalMode {
public:
  /**
   * @brief RMC支持的各类计算模式
   */
  enum p_eMode {
    CriticalMode = 1,         /**< 临界模式 */
    BurnupMode = 2,           /**< 燃耗模式 */
    PointBurnMode = 3,        /**< 点燃耗模式 */
    FixedSourceMode = 4,      /**< 固定源模式 */
    QuasiStaticSMode = 5,     /**< 准静态动力学初始步模式 */
    QuasiStaticDMode = 6,     /**< 准静态动力学动态步模式 */
    KineticsMode = 7          /**< 随机中子动力学模式 */
  };
  /**
   * @brief 当前粒子输运类型
   */
  int p_nParticleMode = NeutronMode;
  /**
   * @brief RMC支持的各类粒子输运类型，包括单一粒子输运及耦合粒子输运
   */
  enum p_eParticleMode {
    NeutronMode = 1,               /**< 中子模式 */
    NeutronPhotonMode = 2,         /**< 中光子模式 */
    PhotonMode = 3,                /**< 光子模式 */
    PhotonElectronMode = 4,        /**< 光电模式 */
    ElectronMode = 5,              /**< 电子模式 */
    NeutronPhotonElectronMode = 6  /**< 中光电模式 */
  };
  /**
   * @brief 当前RMC的计算类型
   */
  int p_nRmcCalcMode = -1;
  /**
   * @brief 是否跳过输运计算，仅用于画图功能
   */
  bool p_bSkipCalculation = false;
  /**
   * @brief DAGMC计算模式
   */
  bool p_bDagmc = false;

  /**
   * @brief RMC支持的中子减方差计算模式
   * @details 包括栅元重要性、栅元权窗、网格权窗
   */
  enum NeutronVarianceReductionMode {
    CellImportance = 1,    /**< 栅元重要性 */
    CellWeightWindow = 2,  /**< 栅元权窗 */
    TrackMeshWeightWindow = 3,   /**< 针对轨迹的网格权窗 */
    PointMeshWeightWindow = 4 /**< 基于点的网格权窗 */
  };
  /**
   * @brief RMC支持的光子减方差计算模式
   * @details 包括栅元重要性、栅元权窗、网格权窗
   */
  enum PhotonVarianceReductionMode {
    CellImportanceGma = 1,   /**< 栅元重要性 */
    CellWeightWindowGma = 2, /**< 针对轨迹的网格权窗 */
    TrackMeshWeightWindowGma = 3,  /**< 针对轨迹的网格权窗 */
    PointMeshWeightWindowGma = 4 /**< 基于点的网格权窗 */
  };
  /**
   * @brief RMC支持的电子减方差计算模式
   * @details 包括栅元重要性、栅元权窗、网格权窗
   */
  enum ElectronVarianceReductionMode {
    CellImportanceElectron = 1,   /**< 栅元重要性 */
    CellWeightWindowElectron = 2, /**< 栅元权窗 */
    TrackMeshWeightWindowElectron = 3,  /**< 针对轨迹的网格权窗 */
    PointMeshWeightWindowElectron = 4 /**< 基于点的网格权窗 */
  };
  /**
   * @brief 当前计算中使用的减方差模式,按照粒子顺序来排序 中子-光子-电子-正电子
   */
  vector<int>p_nVarRedMode = {0,
                              NeutronVarianceReductionMode::CellImportance,
                              PhotonVarianceReductionMode::CellImportanceGma,
                              ElectronVarianceReductionMode::CellImportanceElectron,
                              ElectronVarianceReductionMode::CellImportanceElectron //目前暂时不支持正电子
                             };


  /**
   * @brief 调整权重下限的标识
   * @details 目前仅支持标识2，表明在减方差计算中，减小了中子和光子的权重下限
   */
  int p_nChangeNeuCutWgt = 0.0;

  /**
   * @brief 根据计算模式，执行对应的计算函数
   * @param cCalMode 计算模式
   * @param cNeutronTransport 中子输运
   * @param cPhotonTransport 光子输运
   * @param cElectronTransport 电子输运
   * @param cAceData ACE截面数据
   * @param cGeometry 几何
   * @param cDepth 燃耗
   * @param cCriticality 临界
   * @param cMaterial 材料
   * @param cParticleState 粒子状态
   * @param cConvergence 源收敛
   * @param cTally 计数器
   * @param cBurnup 燃耗
   * @param cFixedSource 固定源
   * @param ORNG 随机数发生器
   * @param cME 矩阵
   * @param cTTA TTA方法
   * @param cAdjoint 伴随
   * @param cExternalSource 通用外源
   * @param cSampling 随机抽样
   * @param cKinetics 动力学对象
   * @param cPerturb 微扰对象
   */
  void RunCalculation(CDCalMode &cCalMode, CDNeutronTransport cNeutronTransport, CDPhotonTransport &cPhotonTransport,
                      CDElectronTransport &cElectronTransport, CDAceData &cAceData, CDGeometry cGeometry,
                      Depth_Class &cDepth, CDCriticality cCriticality, CDMaterial cMaterial,
                      CDParticleState cParticleState, CDConvergence cConvergence, CDTally cTally, CDBurnup cBurnup,
                      CDFixedSource &cFixedSource, CDRNG &ORNG, ME_Class &cME, TTA_Class &cTTA, CDAdjoint &cAdjoint,
                      CDExternalSource &cExternalSource, CDSampling cSampling, CDKinetics &cKinetics,
                      CDPerturbation &cPerturb);

  /**
   * @brief 对所有需要修正的随机介质区域内的弥散颗粒实际填充率进行判断是否达到填充率精度要求，
   *        若精度要求满足返回true
   * @param cGeometry 几何类对象，此函数需要用到随机介质相关的几何信息来读取弥散颗粒填充率
   * @param vParticlePreFrac 所有需要修正的随机介质区域内的弥散颗粒实际填充率
   * @param vUnivIndex 所有需要修正的随机介质区域几何空间编号
   * @return 是否达到填充率精度要求
   */
  bool CheckPackConvergence(CDGeometry cGeometry,
                            vector<vector<double>> vParticlePreFrac,
                            vector<int> vUnivIndex);

private:
  /**
   * @brief 进行临界计算
   * @note 对于ORNG的传递问题，由于OpenMP不能够将引用变量设置为private，
   *   所以临界计算和燃耗计算都采用值传递，后续如果固定源计算也需要实现OpenMP，
   *   则也需要改为使用值传递ORNG。
   * @param cCalMode 计算模式
   * @param cFixedSource 固定源
   * @param cNeutronTransport 中子输运
   * @param cPhotonTransport 光子输运
   * @param cElectronTransport 电子输运
   * @param cAceData ACE截面数据
   * @param cCriticality 临界
   * @param cMaterial 材料
   * @param cGeometry 几何
   * @param cParticleState 粒子信息
   * @param cConvergence 收敛
   * @param cTally 计数器
   * @param cBurnup 燃耗
   * @param ORNG 随机数
   * @param cAdjoint 伴随
   * @param cSampling 随机抽样
   * @param cExternalSource 通用外源
   * @param cPerturb 微扰
   */
  void CalcCriticality(CDCalMode &cCalMode, CDFixedSource &cFixedSource, CDNeutronTransport cNeutronTransport,
                       CDPhotonTransport &cPhotonTransport, CDElectronTransport &cElectronTransport,
                       CDAceData &cAceData, CDCriticality cCriticality, CDMaterial cMaterial, CDGeometry cGeometry,
                       CDParticleState cParticleState, CDConvergence cConvergence, CDTally cTally, CDBurnup cBurnup,
                       CDRNG ORNG, CDAdjoint &cAdjoint, CDSampling &cSampling, CDExternalSource &cExternalSource,
                       CDPerturbation &cPerturb);

  /**
   * @brief 进行固定源计算
   * @param cCalMode 计算模式
   * @param cNeutronTransport 中子输运
   * @param cPhotonTransport 光子输运
   * @param cElectronTransport 电子输运
   * @param CAceData ACE截面数据
   * @param cFixedSource 固定源
   * @param CMaterial 材料
   * @param cGeometry 几何
   * @param cParticleState 粒子信息
   * @param CTally 计数器
   * @param ORNG 随机数
   * @param cCriticality 临界
   * @param cExternalSource 通用源
   * @param cSampling 随机抽样
   * @param cPerturb 微扰对象
   */
  void
  CalcFixedSource(CDCalMode &cCalMode, CDNeutronTransport &cNeutronTransport, CDPhotonTransport &cPhotonTransport,
                  CDElectronTransport &cElectronTransport, CDAceData &CAceData, CDFixedSource &cFixedSource,
                  CDMaterial &CMaterial, CDGeometry &CGeometry, CDParticleState &CParticleState, CDTally &CTally,
                  CDRNG &ORNG, CDCriticality &cCriticality, CDExternalSource cExternalSource, CDSampling &cSampling,
                  CDPerturbation &cPerturb);

  // One-time initialization; not a repeated-run reset.
  void InitializeFixedSourceModel(CDCalMode &cCalMode, CDNeutronTransport &cNeutronTransport,
                                          CDPhotonTransport &cPhotonTransport, CDElectronTransport &cElectronTransport,
                                          CDAceData &CAceData, CDFixedSource &cFixedSource, CDMaterial &CMaterial,
                                          CDGeometry &CGeometry, CDParticleState &CParticleState, CDTally &CTally,
                                          CDBurnup &CBurnup, CDRNG &ORNG, CDSampling &cSampling,
                                          CDPerturbation &cPerturb);

  // Requires initialized model and explicitly prepared run state.
  void ExecuteFixedSourcePrepared(CDCalMode &cCalMode, CDNeutronTransport &cNeutronTransport,
                                CDPhotonTransport &cPhotonTransport, CDElectronTransport &cElectronTransport,
                                CDAceData &CAceData, CDFixedSource &cFixedSource, CDMaterial &CMaterial,
                                CDGeometry &CGeometry, CDParticleState &CParticleState, CDTally &CTally,
                                CDRNG &ORNG, CDCriticality &cCriticality, CDExternalSource &cExternalSource,
                                CDSampling &cSampling, CDPerturbation &cPerturb);

  // Complete statistics once; ordinary output remains in CalcFixedSource.
  void FinalizeFixedSourceRun(CDFixedSource &cFixedSource, CDMaterial &CMaterial,
                                      CDAceData &CAceData, CDTally &CTally);

  /**
   * @brief 进行燃耗计算
   * @param cCalMode 计算模式
   * @param cNeutronTransport 中子输运
   * @param cPhotonTransport 光子输运
   * @param cAceData ACE截面数据
   * @param cCriticality 临界
   * @param cMaterial 材料
   * @param cGeometry 几何
   * @param cParticleState 粒子状态信息
   * @param cConvergence 源收敛
   * @param cTally 计数器
   * @param cBurnup 燃耗
   * @param ORNG 随机数
   * @param cAdjoint 伴随
   * @param cSampling 随机抽样
   * @param cElectronTransport 电子输运
   * @param cFixedSource 固定源
   * @param cExternalSource 通用外源
   * @param cPerturb 微扰
   */
  void CalcBurnup(CDCalMode &cCalMode, CDNeutronTransport cNeutronTransport, CDPhotonTransport &cPhotonTransport,
                  CDAceData &cAceData, CDCriticality cCriticality, CDMaterial cMaterial, CDGeometry cGeometry,
                  CDParticleState cParticleState, CDConvergence cConvergence, CDTally cTally, CDBurnup cBurnup,
                  CDRNG ORNG, CDAdjoint cAdjoint, CDSampling &cSampling, CDElectronTransport &cElectronTransport,
                  CDFixedSource &cFixedSource, CDExternalSource &cExternalSource, CDPerturbation &cPerturb);

  /**
   * @brief 进行点燃耗计算
   * @param cDepth 燃耗
   * @param cME 矩阵
   * @param cTTA TTA算法
   */
  void CalcPointBurnup(Depth_Class &cDepth, ME_Class &cME, TTA_Class &cTTA);

  /**
   * @brief 此函数实现随机介质隐式方法自动迭代修正功能,通过构建无材料的假输运过程，统计中子的通量（即体积）,从而
   *        获取弥散颗粒的实际填充率。中子在输运过程中由于没有材料（相当于真空）,中子仅仅穿面，无碰撞. 输运开始前首先
   *        获取需要进行填充率修正的随机介质空间，对该空间建立相应的计数器。当每次输运结束统计通量，用颗粒内的通量除以
   *        随机介质区域的总通量，获取填充率。
   *        下一次修正填充率 = 当前修正填充率 * （目标填充率/实际填充率），当实际填充率与目标填充率相对误差小于0.5%时，迭代修正过程
   *        结束。
   * @param cCalMode 计算模式对象,此函数新增加了随机介质隐式方法自动修正计算模式
   * @param cFixedSource 固定源对象
   * @param cNeutronTransport 中子输运对象
   * @param cPhotonTransport 光子输运对象
   * @param cElectronTransport 电子输运对象
   * @param cPerturb 微扰对象
   */
  static void CLSCorrection(CDCalMode &cCalMode, CDFixedSource &cFixedSource, CDNeutronTransport cNeutronTransport,
                            CDPhotonTransport &cPhotonTransport, CDElectronTransport &cElectronTransport,
                            CDAceData &cAceData, CDCriticality cCriticality, CDMaterial cMaterial, CDGeometry &cGeometry,
                            CDParticleState cParticleState, CDConvergence cConvergence, CDTally cTally, CDRNG ORNG,
                            CDAdjoint &cAdjoint, CDSampling &cSampling, CDExternalSource &cExternalSource,
                            CDPerturbation &cPerturb);

  /**
   * @brief 统计燃耗信息，将均匀化组件的通量分布/燃耗分布/功率分布进行H5输出
   * @param cBurnup 燃耗模块
   * @param cGeometry 几何模块
   * @param cTally 统计模块
   */
  void GetBurnupInfo(CDBurnup &cBurnup, CDGeometry &cGeometry, CDTally cTally);

  /**
   * @brief 随机中子动力学计算,计算模式目前包括点火概率,脉冲引发时间
   * @param cNeutronTransport 中子输运对象
   * @param cAceData ACE截面数据
   * @param cKinetics 随机中子动力学参数
   * @param cMaterial 材料
   * @param cGeometry 几何
   * @param cParticleState 粒子状态信息
   * @param cTally 计数器
   * @param ORNG 随机数
   * @param cExternalSource 通用源
   */
  void CalcKinetics(CDNeutronTransport &cNeutronTransport, CDAceData &cAceData, CDKinetics &cKinetics,
                    CDMaterial &cMaterial, CDGeometry &cGeometry,
                    CDParticleState &cParticleState, CDTally &cTally, CDRNG &ORNG, CDExternalSource &cExternalSource, CDSampling &cSampling,
                    CDBurnup cBurnup);

public:
  /**
   * @brief 构造函数
   */
  CDCalMode() = default;
};

extern CDCalMode OCalMode;

#endif
