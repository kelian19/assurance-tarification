export const profiles = {
 standard: {label:'Conducteur expérimenté', frequency:0.08, severity:2500},
 young: {label:'Jeune conducteur', frequency:0.15, severity:2800},
 urban: {label:'Conducteur en zone urbaine', frequency:0.11, severity:2600}
};
function finite(v, name, min=0) { if(typeof v !== 'number'||!Number.isFinite(v)||v<min) throw new Error(`${name} : valeur invalide.`); }
export function calculate({frequency,severity,beta=4,k=4,history=[],method='bayes',coverage=1,fixedFee=0,expenseRate=0,marginRate=0}) {
 finite(frequency,'Fréquence',Number.MIN_VALUE); finite(severity,'Coût moyen',Number.MIN_VALUE);
 finite(beta,'Force du tarif initial',Number.MIN_VALUE); finite(k,'Paramètre de crédibilité',Number.MIN_VALUE);
 finite(coverage,'Durée du contrat',Number.MIN_VALUE); if(coverage>1)throw new Error('La durée du contrat doit être de 12 mois au maximum.');
 finite(fixedFee,'Frais fixes'); finite(expenseRate,'Taux de frais'); finite(marginRate,'Taux de marge');
 if(expenseRate+marginRate>=1)throw new Error('La somme des taux de frais et de marge doit être inférieure à 100 %.');
 if(!['prior','bayes','credibility'].includes(method))throw new Error('Méthode inconnue.');
 let t=0,n=0,s=0;
 for(const row of history){finite(row.exposure,'Exposition');finite(row.claims,'Nombre de sinistres');finite(row.amount,'Charge totale');
 if(row.exposure>1)throw new Error('Une ligne d’historique représente au maximum une année.');
 if(!Number.isInteger(row.claims))throw new Error('Le nombre de sinistres doit être entier.');
 if(row.exposure===0&&(row.claims>0||row.amount>0))throw new Error('Un historique de sinistres doit avoir une durée assurée positive.');
 if(row.claims===0&&row.amount>0)throw new Error('Une charge positive nécessite au moins un sinistre.');
 t+=row.exposure;n+=row.claims;s+=row.amount;}
 const prior=frequency*severity, alpha=frequency*beta;
 const posteriorFrequency=(alpha+n)/(beta+t), bayes=posteriorFrequency*severity;
 const zBayes=t/(beta+t),zCredibility=t/(k+t);
 const credibility=t? (1-zCredibility)*prior+zCredibility*s/t:prior;
 const annualPure={prior,bayes,credibility}[method];
 const periodPure=annualPure*coverage;
 const premium=(periodPure+fixedFee)/(1-expenseRate-marginRate);
 return {prior,bayes,credibility,alpha,beta,posteriorAlpha:alpha+n,posteriorBeta:beta+t,posteriorFrequency,zBayes,zCredibility,t,n,s,annualPure,periodPure,premium,monthly:premium/(coverage*12),expenses:premium*expenseRate+fixedFee,margin:premium*marginRate,change:(annualPure/prior-1)*100};
}
