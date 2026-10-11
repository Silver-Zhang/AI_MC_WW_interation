from pathlib import Path
import json,subprocess,re,difflib,sys
T=Path(__file__).resolve().parents[1];label=sys.argv[1] if len(sys.argv)>1 else 'exports-01';root=T/'logs'/label/'ff';results=[]
suffix=['FOM','Fluctuated_FOM','Batches_of_FOM','TenStatisticsChecks/FoMValueCheck','TenStatisticsChecks/FoMBehaviourCheck']
parents={'/Tally/CellTally3/Cell1/TotalBin'}|{f'/Tally/MeshTally2/Bin{i}' for i in range(124)}
allowed={p+'/'+s for p in parents for s in suffix}
def read(path):
 names=subprocess.check_output(['h5dump','-n',str(path)],text=True)
 paths={l.strip().removeprefix('dataset').strip() for l in names.splitlines() if 'dataset' in l}
 selected={p for p in paths if any(p.endswith('/'+s) for s in suffix)}
 assert selected<=allowed,selected-allowed
 raw=subprocess.check_output(['h5dump','-m','%.17g','-y','-w','0',str(path)],text=True)
 raw=re.sub('^HDF5 "[^"]*"','HDF5 "<file>"',raw)
 pattern=r'(DATASET "(?:FOM|Fluctuated_FOM|Batches_of_FOM|FoMValueCheck|FoMBehaviourCheck)" \{\s*DATATYPE[^\n]*\n\s*DATASPACE[^\n]*\n\s*DATA \{)\n.*?\n(\s*\}\n\s*\})'
 normal,count=re.subn(pattern,r'\1\n <predeclared-time-field>\n\2',raw,flags=re.S);assert count==len(selected)
 return normal,sorted(selected),len(paths)
for n in [1,2]:
 p=root/'persistent'/f'{n}-result.h5';f=root/f'fresh-{n}'/'1-result.h5';a,paths,na=read(p);b,fpaths,nb=read(f)
 same=a==b and paths==fpaths;pdf=json.loads((p.parent/f'{n}-pdf.json').read_text())==json.loads((f.parent/'1-pdf.json').read_text())
 if not same:(root/f'{n}-hdf.diff').write_text(''.join(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='fresh',tofile='persistent')))
 results.append({'run':n,'hdf_pass':same,'all_emitted_pdf_pass':pdf,'persistent_datasets':na,'fresh_datasets':nb,'time_exceptions':paths})
(root/'comparison.json').write_text(json.dumps(results,indent=2));print([{k:v for k,v in x.items() if k!='time_exceptions'} for x in results]);sys.exit(not all(x['hdf_pass'] and x['all_emitted_pdf_pass'] for x in results))
