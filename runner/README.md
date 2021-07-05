# Continuous Integration (CI) script and config

This folder contains files needed for the CI.

## Building the Gitlab CI file

To separate the different years and survey files we have a script that build the CI script.

```
python runner/build_ci.py
```

It will create the file `.gitlab-ci.yml` that is read by Gitlab Runner to execute the CI.