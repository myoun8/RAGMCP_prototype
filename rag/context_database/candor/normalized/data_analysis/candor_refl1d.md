---
doc_id: candor_refl1d_fitting
source_id: CANDOR-003
title: Refl1D — Fitting Guide
instrument: CANDOR
workflow_stage: data_analysis_model_fitting
source_type: documentation_page
access_level: public
status: current
owner: Refl1D / reflectometry community
last_reviewed: 2026-06-15
source_url_or_path: https://refl1d.readthedocs.io/en/latest/guide/fitting.html
source_last_updated: unknown
citation_required: true
---

# Refl1D — Fitting Guide

This page documents practical fitting workflows for Refl1D, especially optimization, uncertainty analysis, posterior interpretation, and reporting of reflectometry model results. It is relevant to CANDOR data analysis because Refl1D is used for reflectometry model fitting and uncertainty assessment.

## Core fitting principle

A good fit depends first on having the correct physical model. Fitting problems often come from model structure rather than optimizer choice:

- too many or too few layers;
- fit ranges that are too narrow or too unconstrained;
- missing layers, such as an SiOx layer on a silicon substrate;
- systematic data effects, including sample warp, alignment offsets, and finite resolution near the critical edge.

Important Refl1D adjustments mentioned in the source:

- Use `sample_broadening=value` when a warped sample broadens the resolution near the critical edge.
- Fit `probe.theta_offset` when sample or slit alignment shifts the measured critical edge.
- Use `refl1d.probe.Probe.critical_edge()` to increase computation density near the critical edge.
- Use `refl1d.probe.Probe.over_sample()` for thick samples where resolution integrates over multiple Kiessig fringes and aliasing is possible.

## Quick fit workflow

For rapid model development, the guide recommends the Nelder-Mead simplex algorithm (`fit=amoeba`). Use roughly 1000–3000 steps and multiple restarts. In the GUI, `starts=1` and repeated use of the fit button can work well for incremental model improvement.

Example command:

```bash
refl1d --fit=amoeba --steps=1000 --starts=20 --parallel model.py --store=T1
```

Improve a command-line fit by restarting from the previous parameter file:

```bash
refl1d --fit=amoeba --steps=1000 --starts=20 --parallel model.py --store=T1 --pars=T1/model.par
```

Alternative quick optimizers:

- `fit=de` — differential evolution; more likely than amoeba to find a global minimum, but slower.
- `fit=rl` — random lines; can be fast with large populations but may miss isolated minima.

Example commands:

```bash
refl1d --fit=de --steps=3000 --parallel model.py --store=T1
refl1d --fit=rl --steps=3000 --starts=200 --reset --parallel model.py --store=T1
```

Note: the source HTML shows `--parellel` in one random-lines command; this appears to be a typo. Use `--parallel`.

## Uncertainty analysis with DREAM

The guide emphasizes that uncertainty estimates are more important than the single best-fit parameter set. Refl1D uses Bayesian uncertainty analysis by treating the problem as the likelihood of observing the data given a model.

Uncertainty analysis is performed with DREAM (`fit=dream`), a Markov chain Monte Carlo method using a differential-evolution step generator. DREAM explores parameter space by random walk: it always accepts better points and sometimes accepts worse points depending on the likelihood penalty.

DREAM initialization options:

- `init=random` — uniform random initial points across parameter ranges.
- `init=lhs` — Latin hypercube sampling; ensures coverage of subranges for each variable.
- `init=cov` — covariance population from the uncertainty ellipse near the starting point; can fail if the covariance matrix is singular because parameters are highly correlated.
- `init=eps` — epsilon-ball population near the initial point; useful when DREAM fails to converge from a diverse population.

Common DREAM command:

```bash
refl1d --fit=dream --burn=1000 --steps=1000 --init=cov --parallel --pars=T1/model.par model.py --store=T2
```

### DREAM output files to preserve

- `T1/model.err` — table of parameter statistics: mean(std), median, best value, and 68% / 95% credible intervals.
- `T1/model-var.png` — marginal parameter histograms; range shows 95% credible interval and shading shows 68% credible interval.
- `T1/model-corr.png` — parameter correlation plots.
- `T1/model-errors.png` — uncertainty plots from posterior samples, including reflectivity/profile uncertainty.
- `T1/model-trace.png` — trace plot for the first fitting parameter; good mixing should show no chains stuck in separate local minima.
- `T1/model-logp.png` — convergence plot for log-likelihood values; a flat plot indicates convergence, while an upward sweep indicates insufficient burn-in.

### Interpreting DREAM statistics

The source warns that mean and standard deviation are not robust if the Markov process has not converged. Outliers, multi-modal distributions, long tails, or insufficient burn-in can distort the reported values.

The source explains compact uncertainty notation: `24.9(28)` means `24.9 ± 2.8`.

For two digits of precision on the 95% credible interval, the guide says approximately 1,000,000 draws from the distribution are required:

```text
steps = 1000000 / (#parameters * #pop)
```

### Extending DREAM runs

If burn-in was insufficient or sampling is sparse, extend the analysis with `--resume`. Example:

```bash
refl1d --fit=dream --burn=500 --steps=1600 --parallel --resume=T2 --store=T3
```

The guide notes that this example generates additional posterior samples and applies extra burn-in to remove an initial upward sweep in the log-likelihood plot.

## Using the posterior distribution

Posterior analysis can be done after the DREAM run by loading the DREAM state:

```python
from bumps.dream.state import load_state
state = load_state(modelname)
state.mark_outliers()  # ignore outlier chains
state.show()           # plot statistics
```

Restrict variables to selected ranges before plotting:

```python
from bumps.dream import views
selection = {2: (0.8, 1.0), 4: (0.2, 0.4)}
views.plot_vars(state, selection=selection)
views.plot_corrmatrix(state, selection=selection)
```

Add derived variables to posterior plots:

```python
state.derive_vars(lambda p: p[0] + p[1], labels=["x+y"])
state.derive_vars(lambda p: (p[0] * p[1], p[0] - p[1]), labels=["x*y", "x-y"])
state.show()
```

## Reporting results

The guide warns not to claim that a model is uniquely correct. A safer claim is that the observed data are consistent with the model and parameter values. Other models within the search space may fit equally well but remain undiscovered.

Signals of a well-behaved fit include:

- marginal maximum likelihood follows marginal probability density;
- log likelihood is flat, not sweeping upward;
- parameter traces show good mixing;
- marginal probability density is unimodal and roughly normal;
- joint probabilities show no problematic correlation structure;
- chi-squared is approximately 1;
- residuals show no structure.

Suggested reporting language, normalized from the source:

> Refl1D was used to model the reflectivity data. The sample depth profile is represented as slabs with varying scattering length density and thickness, with Gaussian interfaces between slabs. Reflectivity is computed using the Abeles optical matrix method, with interfacial effects computed using the Nevot-Croce method or by approximating interfaces as thin slabs. Refl1D supports simultaneous refinement of multiple reflectivity data sets with constraints between models.
>
> Refl1D uses a Bayesian approach to determine model-parameter uncertainty. By representing the problem as the likelihood of observing the measured reflectivity curve for a given parameter set, Refl1D can use Markov chain Monte Carlo methods to sample the joint parameter probability distribution. This sample is then used to estimate the probability distribution for each parameter.

When reporting maximum likelihood and credible intervals:

> Reported parameter values are taken from the model that best fits the data, with uncertainty determined from the parameter-value range covering 68% of the posterior sample set. This corresponds to a 1-sigma uncertainty level if the sample set is normally distributed.

When reporting mean and standard deviation:

> Reported parameter values are computed from the mean and standard deviation of the posterior sample set. This corresponds to the best-fitting normal distribution to the marginal probability distribution for each parameter.

Caveat: mean and standard deviation can be misleading when burn-in is insufficient, the distribution is multi-modal, or the distribution has long tails.

## Publication graphics

For publication-quality plots, the guide recommends writing scripts that load both the model and fit results. Basic pattern:

```python
import sys
import os.path
from bumps.fitproblem import load_problem
from bumps.cli import load_best

model, store = sys.argv[1:3]
problem = load_problem(model)
load_best(problem, os.path.join(store, model[:-3] + ".par"))
print("chisq %s" % problem.chisq_str())
```

Run plotting scripts through Refl1D:

```bash
refl1d -p plot.py model.py X5
```

Useful objects and methods:

- `problem.fitness` — experiment object for simple `FitProblem` models.
- `problem.models[k].fitness` — experiment object for model `k` in multi-model problems.
- `experiment.smooth_profile(dz=0.2)` — generates SLD profile arrays.
- `experiment.reflectivity()` — returns reflectivity theory.
- `experiment.probe` — provides `Q`, `dQ`, `R`, `dR`, `T`, `dT`, `L`, `dL`, and plotting methods.
- `bumps.dream.state.load_state()` — reloads DREAM MCMC samples.
- `bumps.errplot.calc_errors_from_state()` — computes profile and residual uncertainty samples.
- `refl1d.uncertainty.align_profiles()` — aligns sampled profiles for comparison.

For profile-error plots aligned to an interface, use `align_errors()` from `refl1d.names` or run:

```bash
refl1d align.py <model>.py <store> [<align>] [1|2|n]
```

Alignment options:

- `auto` — default behavior.
- integer interface number — align on an interface.
- half-integer such as `2.5` — align on the center of a layer.
- prefix `R` — count interfaces from the surface, e.g., `R1`.

Plot output is saved as:

```text
<store>/<model>-err#.png
```

## Tough fits

For difficult fits, especially freeform models with many control points, the guide identifies parallel tempering (`fit=pt`) as the most promising approach. Parallel tempering extends DREAM by running multiple temperatures concurrently. High-temperature chains can cross barriers between minima, while low-temperature chains aggressively seek local minima.

The implementation described uses fixed temperatures from `Tmin=0.1` to `Tmax=10` in `nT=25` steps. The guide notes that future versions should adapt temperature to the fitting problem.

Important limitation: parallel tempering does not yet generate the uncertainty plots provided by DREAM.

## Command-line notes

The GUI is slower because it frequently updates graphs of the current best fit. For overnight model batches, create a batch file with one command per model and append `--batch` so Refl1D does not stop for interactive graphs.

View fitted results in the GUI:

```bash
refl1d --edit model.py --pars=T1/model.par
```

## Other optimizers

The guide lists several less commonly used optimizers:

- `fit=newton` / BFGS — quasi-Newton optimizer; often not robust for reflectometry because correlated parameters can make numerical derivative matrices ill-conditioned.
- `fit=ps` / particle swarm optimization — population-based, but appears weak for high-dimensional reflectivity problems.
- `fit=snobfit` — constructs a locally quadratic model of the search space; promising in principle, but not yet tuned for reflectivity and performed poorly in initial trials.

## References preserved from source

- WH Press, BP Flannery, SA Teukolsky, WT Vetterling, *Numerical Recipes in C*, Cambridge University Press.
- I. Sahin (2011), “Random Lines: A Novel Population Set-Based Evolutionary Global Optimization Algorithm,” *Lecture Notes in Computer Science*, 6621, 97–107. DOI:10.1007/978-3-642-20407-4_9.
- J. A. Vrugt et al. (2009), “Accelerating Markov chain Monte Carlo simulation by differential evolution with self-adaptive randomized subspace sampling,” *Int. J. Nonlin. Sci. Num.*, 10, 271–288.
- J. Kennedy and R. Eberhart (1995), “Particle Swarm Optimization,” *Proceedings of IEEE International Conference on Neural Networks*, IV, 1942–1948. DOI:10.1109/ICNN.1995.488968.
- W. Huyer and A. Neumaier (2008), “Snobfit — Stable Noisy Optimization by Branch and Fit,” *ACM Transactions on Mathematical Software*, 35, Article 9.
- R. Storn (1996), “System Design by Constraint Adaptation and Differential Evolution,” Technical Report TR-96-039, International Computer Science Institute.
- R. H. Swendsen and J. S. Wang (1986), “Replica Monte Carlo simulation of spin glasses,” *Physical Review Letters*, 57, 2607–2609.

<!-- Source: Fitting — Refl1D 1.0.2a0.post9+g00f367ec documentation (https://refl1d.readthedocs.io/en/latest/guide/fitting.html). Saved HTML from Read the Docs/Refl1D documentation. Styling, navigation, search, Read the Docs widgets, EthicalAds content, generated CSS, MathJax boilerplate, and repeated page chrome removed. Important fitting commands, uncertainty-analysis guidance, output-file meanings, posterior-analysis snippets, reporting language, publication-graphics workflow, optimizer notes, and references preserved. Source page last-updated date was not present in the saved HTML. -->
