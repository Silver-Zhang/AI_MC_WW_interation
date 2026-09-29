/// @file
/// @copyright Copyright (c) 2000-2026 REAL Tsinghua University. All Rights Reserved.

# include "CalMode.h"
# include "Input.h"
# include "PhotonTransport.h"
# include "ElectronTransport.h"
# include "Utility/Timer.h"
# include "Utility/IO/Logger.h"

#ifdef DEBUG_ATTACH
#include "Utility/Debug/DebugUtility.h"
#endif

#ifdef USE_SIGHANDLER
#include "Utility/Signal/SignalHandler.h"
#ifdef PERSONAL_USE
#ifdef USE_WINDOWS
#include <process.h>
#endif
#endif
#endif

# include "Status.h"
# include "Control/Control.h"

//////////  Global classes  //////////
CDOutput Output;
CDMeshInfo OMeshInfo;
CDXSParaTableVec OXSParaTableVec;
CDWeightWindow OWeightWindow;
CDStatus OStatus;
Utility::RMCTimer OTimer;
CellVector cellVec;
CDPTRAC OParticleTracker;
RMC::Control OController;
CDRNG ORNG;
CDCalMode OCalMode;
namespace RMC {
  namespace IO {
    Logger OLogger; // NOLINT(cert-err58-cpp)
    Logger OProcLogger; // NOLINT(cert-err58-cpp)
  }
}
using RMC::IO::OLogger;
using RMC::IO::OProcLogger;

# ifdef USE_PYTHON_API
# include "PythonInterface.h"
CDPythonInterface OPythonInterface;
# endif

# ifdef USE_MPI
CDParallel OParallel;
# endif

int main(int argc, char *argv[]) {
#ifdef RMC_F11_PROBE
  f11_probe::mark("main.enter");
#endif
  ///////////////// Define objects ////////////////////////
  ///////  decoupling via refactoring at 20130720   ///////
  CDRNG ORNG;
  CDInput OInput;
  CDGeometry OGeometry;
  CDMaterial OMaterial;
  CDAceData OAceData;
  CDCriticality OCriticality;
  CDBurnup OBurnup;
  CDTally OTally;
  CDConvergence OConvergence;
  CDParticleState OParticleState;
  CDPlot OPlot;
  CDFixedSource OFixedSource;
  CDExternalSource OExternalSource;
  CDNeutronTransport ONeutronTransport;
  CDPhotonTransport OPhotonTransport;
  CDElectronTransport OElectronTransport;
  CDAdjoint OAdjoint;
  CDSampling OSampling;
  CDKinetics OKinetics;
  CDPerturbation OPerturb;

  ////Classes just for PointBurnUp Mode///////
  Depth_Class ODepth;
  TTA_Class OTTA;
  ME_Class OME;

  //// Classes for group constant generation
  CDGroupConstant OGroupConstant;
  CDHomogenization OHomogenization;

  ///////////////// Parallel Case ////////////////////////
# ifdef USE_MPI
  MPI_Init(&argc, &argv);
  OParallel.InitiateParallel();
# endif

#ifdef DEBUG_ATTACH
  Utility::Debug::PauseProcessToWaitForAttaching();
#endif

#ifdef USE_SIGHANDLER
#ifdef USE_UNIX
  Utility::Handler::InitSigHandler();
#endif
#endif

#ifdef BACKTRACE
  Utility::Handler::SetBACKTRACEHandler();
#endif

#ifdef CATCH_ERROR
  Utility::Handler::SetCATCHERRORHandler();
#endif

#ifdef PERSONAL_USE
#ifdef USE_WINDOWS
  _beginthread(reinterpret_cast<void (*)(void *)>(Utility::Handler::StartAlarm), 0, NULL);
#else
  Utility::Handler::StartAlarm();
#endif

# endif

  /////////Check command line and inp file exist: start ////////////
  OInput.CheckIOFile(argc, argv);

  /// Set Logger ///
  OLogger.init_logger(Output.p_chOutputFileName);
  OLogger.SetDefaultLogLevel(RMC::IO::LogLevel::info);
  OLogger.SetDefaultTarget(RMC::IO::LogTarget::ConsoleAndLogFile);
  OProcLogger = OLogger;
  OProcLogger.SetAllowEveryProcLogging(true);

  ////////////// Write output heading ////////////////
  Output.OutputHeading(OCriticality);

  ////////////// Write Status File ///////////////////
  if (OStatus.isPrintStatus()) {
    OStatus.printHeader();
  }

  ////////////// Read input file ////////////////
  OInput.ReadInputBlocks(OCalMode, ONeutronTransport, OPhotonTransport, OElectronTransport, OGeometry,
                         OMaterial, OAceData, OCriticality, OTally, OConvergence, OBurnup, OPlot,
                         OFixedSource, ORNG, OAdjoint, OHomogenization, OExternalSource, OSampling,
                         OKinetics, OPerturb);

  ////////////// Plot Image(geometry) ////////////////
  OPlot.RunPlot(OGeometry, OMaterial, ORNG);

  ////////////// Generate Input File////////////////
  Output.GenerateInpFile(OGeometry, OMaterial, OAceData, OCriticality, OTally, OConvergence,
                         OBurnup, OFixedSource, ORNG, OPerturb);

  ////////////// Run Calculation ////////////////
  OCalMode.RunCalculation(OCalMode, ONeutronTransport, OPhotonTransport, OElectronTransport, OAceData,
                          OGeometry, ODepth, OCriticality, OMaterial,
                          OParticleState, OConvergence, OTally, OBurnup,
                          OFixedSource, ORNG, OME, OTTA, OAdjoint, OExternalSource,
                          OSampling, OKinetics, OPerturb);

  ////////////// Write output ending ////////////////
#ifdef RMC_F11_PROBE
  f11_probe::begin("output.ending");
#endif
  Output.OutputEnding(OCalMode, OAdjoint, OCriticality, OFixedSource);
#ifdef RMC_F11_PROBE
  f11_probe::end("output.ending");
#endif


  ///////////////// Parallel Case ////////////////////////
# ifdef USE_MPI
  MPI_Finalize();
# endif

#ifdef RMC_F11_PROBE
  f11_probe::mark("main.exit");
  f11_probe::flush();
#endif
  return 0;
}
