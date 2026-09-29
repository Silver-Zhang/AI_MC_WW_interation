# Source evidence index

| Topic | Primary current-source evidence |
|---|---|
| globals / main lifetime | `RMC/src/main.cpp:27-55,57-166` |
| dispatch / argument ownership | `RMC/src/RunCalculation.cpp:6-24,83-89` |
| fixed source execution | `RMC/src/CalcFixedSource.cpp:67-180,700-749` |
| fixed-source state | `RMC/src/FixedSource.h:192-418` |
| init / MG adjoint state | `RMC/src/InitiateAll.cpp:125-203`; `RMC/src/InitiateMatAce.cpp:8-126`; `RMC/src/TreatAdjointMaterial.cpp:21-105` |
| batches / source | `RMC/src/InitialBatchSource.cpp:1-344`; `RMC/src/SampleNeutronSource.cpp:180-283` |
| Control scope | `RMC/src/Control/Control.h:15-70`; `RMC/src/Control/Control.cpp:1-28`; `RMC/src/ReadControlBlock.cpp:7-42`; `RMC/src/ReadInputBlocks.cpp:341-347` |
| input dispatch | `RMC/src/ReadInputBlocks.cpp:1-364`; `RMC/src/Input.h:51-71` |
| fixed source parser | `RMC/src/ReadFixedSourceBlock.cpp:6-236` |
| tally ownership | `RMC/src/Tally.h:29-210,964-1030`; `RMC/src/InitiateTally.cpp:57-232`; `RMC/src/ProcessTally.cpp:330-393` |
| mesh field output | `RMC/src/OutputTally.cpp:247-262`; `RMC/src/OutputTallyh5.cpp:57-81`; `RMC/src/MeshTallyHDF5.cpp:40-100` |
| physical MG edges | `RMC/src/CheckMgAceBlock.cpp:38-60`; `RMC/src/GetMgCs.cpp:231-278` |
| WW ownership and update | `RMC/src/WeightWindow.h:61-354`; `RMC/src/ReadWeightWindow.cpp:6-424`; `RMC/src/WeightWindows.cpp:45-100,178-290`; `RMC/src/DoMeshWeightWindow.cpp:21-72` |
| output lifecycle | `RMC/src/CheckIOFile.cpp:135-170`; `RMC/src/OpenFilePtrs.cpp:27-274`; `RMC/src/CloseFilePtrs.cpp:27-74` |
