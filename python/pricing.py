"""Moteur de tarification. Gamma en convention forme/taux ; exposition en années."""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class Period:
    exposure: float
    claims: int
    amount: float = 0.0

def positive(value, name, allow_zero=False):
    if not isinstance(value,(int,float)) or not isfinite(value) or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f'{name} invalide')

def calculate(frequency, severity, history=(), *, beta=4., k=4., method='bayes', coverage=1., fixed_fee=0., expense_rate=0., margin_rate=0.):
    for name,value in [('frequency',frequency),('severity',severity),('beta',beta),('k',k),('coverage',coverage)]:positive(value,name)
    if coverage>1:raise ValueError('coverage doit être au plus égale à 1')
    for name,value in [('fixed_fee',fixed_fee),('expense_rate',expense_rate),('margin_rate',margin_rate)]:positive(value,name,True)
    if expense_rate+margin_rate>=1:raise ValueError('Frais et marge doivent totaliser moins de 100 %')
    if method not in ('prior','bayes','credibility'):raise ValueError('Méthode inconnue')
    t=n=s=0.
    for p in history:
        positive(p.exposure,'exposure',True);positive(p.claims,'claims',True);positive(p.amount,'amount',True)
        if p.exposure>1 or not float(p.claims).is_integer():raise ValueError('Période invalide')
        if not p.exposure and (p.claims or p.amount):raise ValueError('Sinistres sans exposition')
        if not p.claims and p.amount:raise ValueError('Charge sans sinistre')
        t+=p.exposure;n+=p.claims;s+=p.amount
    prior=frequency*severity
    alpha=frequency*beta
    posterior_frequency=(alpha+n)/(beta+t)
    z_bayes=t/(beta+t);z_credibility=t/(k+t)
    bayes=posterior_frequency*severity
    credibility=(1-z_credibility)*prior+z_credibility*s/t if t else prior
    annual={'prior':prior,'bayes':bayes,'credibility':credibility}[method]
    period=annual*coverage
    premium=(period+fixed_fee)/(1-expense_rate-margin_rate)
    if not all(map(isfinite,[annual,premium,prior,bayes,credibility])):raise ValueError('Valeurs hors plage')
    return dict(prior=prior,bayes=bayes,credibility=credibility,annual_pure=annual,period_pure=period,premium=premium,
                posterior_frequency=posterior_frequency,posterior_alpha=alpha+n,posterior_beta=beta+t,
                z_bayes=z_bayes,z_credibility=z_credibility,exposure=t,claims=n,total_amount=s)
