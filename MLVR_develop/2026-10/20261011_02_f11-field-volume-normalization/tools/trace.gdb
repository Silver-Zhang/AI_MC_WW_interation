set pagination off
set confirm off
set print pretty off
set $history = 0
set $uniform = 0
set $heter = 0
break CDFixedSource::TrackHistory
commands
silent
set $history = $history + 1
printf "SOURCE,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n", $history, cParticleState.p_dPos[0], cParticleState.p_dPos[1], cParticleState.p_dPos[2], cParticleState.p_dDir[0], cParticleState.p_dDir[1], cParticleState.p_dDir[2], cParticleState.p_dWgt, cParticleState.p_dErg
continue
end
break CDTally::TallyByTL
commands
silent
printf "SEGMENT,%d,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g,%.17g\n", $history, cParticleState.p_dPos[0], cParticleState.p_dPos[1], cParticleState.p_dPos[2], cParticleState.p_dDir[0], cParticleState.p_dDir[1], cParticleState.p_dDir[2], cParticleState.p_dWgt, cParticleState.p_dErg, dTrackLen
continue
end
break CDMesh::CalcMeshTrck
commands
silent
set $uniform = $uniform + 1
if $uniform == 1
printf "PATH,uniform,usevol=%d,heterflag=%d\n", p_bUseVol, p_bIsHeterMesh
end
continue
end
break CDMesh::CalcHeterMeshTrck
commands
silent
set $heter = $heter + 1
if $heter == 1
printf "PATH,heter,usevol=%d,heterflag=%d\n", p_bUseVol, p_bIsHeterMesh
end
continue
end
break /tmp/f11-volume-rmc-source/src/ProcessTally.cpp:364
commands
silent
printf "DENOM,%.17g,N=%lld\n", cFixedSource.p_dTotStartWgt, cFixedSource.p_llCurTotParNum
continue
end
break CDTallyData::CalcAveRe
commands
silent
printf "AVERAGING,M=%.17g,Div=%.17g\n", dM, dDiv
continue
end
run
printf "COUNTS,histories=%d,uniform=%d,heter=%d\n", $history, $uniform, $heter
quit
