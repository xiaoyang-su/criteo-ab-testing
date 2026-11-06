# Criteo A/B Test Portfolio Project

## 1. Business Problem
In the revised data released by Criteo, did the advertising placement eligibility increase website visits compared to the holdout group? What is the estimated effect size, how accurate is it, and does the conversion result provide further support?

## 2. Architecture
We divides the project for mainly five part, and two more optional:
### 1. Data Integrity & Assignment Diagnostics
Here, we need to check the data integrity and the `exposure` consistency (there are two restrictions: `treatment = 0 ⇒ exposure = 0` and `conversion = 1 ⇒ visit = 1`), allocation audit (A formal SRM assessment was not conclusive because the exact expected allocation probability for the released benchmark sample is unavailable. We therefore report the observed allocation ratio with an assumption-based SRM test and supplement it with covariate balance and treatment-assignment predictability diagnostics.), Covariate Balance (Using SMD on four continious feature `f0`, `f2`, `f7`, `f10`), Treatment Predictability (Optional, using logistic regression).
The output is a `Experiment Validation Report`.

### 2. Statistical Inference
This step is the core step of our project. Here we need to calculate some descriptive statistics (like sample size, successful times and Visit/Conversion Rate), analyse the effect size (Absolute Lift, Relative Lift), do hypothesis testing, check the confidence interval, robustness check (Bootstrap, etc.). 

#### Main Analysis
Here we build the project using randomrized controlled trial (RCT). We used the treatment variable as `treatment` rather `exposure`. This is because it is not randomrized for people to see the advertisement, which will produce selection bias. Besides, we choose `visit` as the primary outcome and use `conversion` as the secondary outcome because it is a downstream business indicator. The evaluatin value is ITT (Intent-to-Treat Effect) as below:
$$
ITT = E[visit | treatment = 1] - E[visit|treatment = 0].
$$
And the ralative lift is 
$$
REL = \frac {E[visit | treatment = 1] - E[visit|treatment = 0]} {E[visit|treatment = 0]}.
$$

The output is a `Experiment Results`.

### 3. Power Analysis & MDE
Base on fixed sample size, baseline and pre-set power to calculate the reverse MDE, and compare different allocation and sample size scenarios.

### 4. Covariate Adjustment & Variance Reduction
Use unadjusted ITT as baseline, and then do regression adjustment and CUPED-style adjustment.

### 5. Parameterized Business Decision Memo
Here we should include executive summary, experiment design, experiment validity, primary results (`visit`), secondary results (`conversion`), power & precision, business impact, limitations, next steps.

### Optional 1. IV/exposure sensitivity analysis
### Optional 2. Uplift Targeting

## 3. Deliverables and Deviation from the Plan