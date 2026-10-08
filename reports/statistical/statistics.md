# Statistical analysis

UK: 5,349 customers; other countries: 516. Mean customer-level invoice difference: GBP -293.98, bootstrap 95% CI [-377.48, -222.53].

Welch p=2.08674e-13, Holm p=2.08674e-13; Mann-Whitney p=7.50249e-44, Holm p=1.5005e-43.

Differences are associations conditional on identified customers. They do not establish an effect of geography. Review wholesale/customer mix before acting.

- Customers treated as independent; shared markets and unknown wholesale relationships may violate this.
- Country comparison is observational and not adjusted for mix, tenure or season.
- Welch permits unequal variances; heavy tails motivate the nonparametric sensitivity test.
- Holm correction covers the two explicitly reported geographic tests.
- Bootstrap intervals describe this sample era, not future prediction intervals.
- Seven-day moving blocks preserve local dependence but not all long-term seasonality.
- Paired tests/ANOVA/chi-square omitted because this predefined contrast does not require them.