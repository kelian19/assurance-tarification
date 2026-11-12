export function predictProfile(profile,model,costIndex=1){
 if(!Number.isFinite(costIndex)||costIndex<.1||costIndex>10)throw new Error('L’indice de coût doit être compris entre 0,1 et 10.');
 const values={};
 for(const [name,edges] of Object.entries(model.bins)){
  const value=profile[name];if(!Number.isInteger(value)||value<edges[0]||value>=edges.at(-1))throw new Error(`${name} : valeur hors du domaine ${edges[0]}–${edges.at(-1)-1}.`);
  for(let i=0;i<edges.length-1;i++)if(value>=edges[i]&&value<edges[i+1]){values[name+'Band']=`${edges[i]}-${edges[i+1]-1}`;break;}
 }
 for(const name of ['VehGas','Area','Region']){
  if(!Object.hasOwn(model.frequency.coefficients[name],profile[name]))throw new Error(`${name} : modalité inconnue.`);
  values[name]=profile[name];
 }
 const glm=which=>Math.exp(model[which].intercept+Object.entries(values).reduce((sum,[key,value])=>sum+model[which].coefficients[key][value],0));
 const frequency=glm('frequency'),severity=(glm('severity')+model.severity_tail)*costIndex;
 const beta=model.frailty_shape_r/frequency,k=beta*model.severity_second_moment_factor;
 return {frequency,severity,beta,k,prior:frequency*severity,version:model.version,costIndex};
}
