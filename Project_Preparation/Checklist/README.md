# Checklist for Forms Extraction

This section serves to provide a generic checklist for the most important aspects of a successful project in this space.

A good starting point is the [Tech Lead's Engineering Fundamentals Checklist](https://github.com/microsoft/code-with-engineering-playbook/blob/master/TECH-LEADS-CHECKLIST.md) from the [CSE code-with-engineering-playbook](https://github.com/microsoft/code-with-engineering-playbook)

## The problem

- [ ] Can the problem to be solved be clearly and succintly defined?
For example, 'We need to extract the following 6 fields from these n forms'
- [ ] Can the success criteria be clearly defined?
For example, 'If the following 6 fields can be extracted 80% of the time from these n forms, then our success criteria are met'.

## The approach

- [ ] Has a hypothesis driven approach been adopted? This is vital for success on any data driven project.

Please refer to [How to Implement Hypothesis-Driven Development](https://www.thoughtworks.com/insights/articles/how-implement-hypothesis-driven-development) as a good example of applying the scientific method to ensure success for a data driven software project.

The steps of the scientific method are to:

- Make observations
- Formulate a hypothesis
- Design an experiment to test the hypothesis
- State the indicators to evaluate if the experiment has succeeded
- Conduct the experiment
- Evaluate the results of the experiment
- Accept or reject the hypothesis
- If necessary, make and test a new hypothesis

## The data

- [ ] Sufficient data exists so that the data may be split into training, test and validation sets.
- [ ] The data available is representative of what is required to be predicted in the production environment.
- [ ] Sufficient labelled or Ground Truth (GT) data exists so that a variety of techniques may be experimented with.
- [ ] The data is accessible to the project team and is compliant with the organisation's security policies.
- [ ] All regulatory constraints on data collection, analysis, or implementation are clear.

## The team

- [ ] Data skills exist within the team to be able to analyse and manipulate the data as needed.
- [ ] At least two data resources are available during the analysis phase to validate each other's work and implement a variety of diverse experimental approaches.

## Additional references

[Fast AI](https://www.fast.ai/) has a fantastic comprehensive [checklist](https://www.fast.ai/2020/01/07/data-questionnaire/) for generic data projects.

Now refer to the [Decision Guidance](../Decision_Guidance/README.md) section to determine whether the Form Recognizer service is a good fit.
