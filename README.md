# QC Collector Template

This repo is intended as a starter template that can be used to create new automated QC collector tools. It follows the 
conventions used by our [routine-sequence-qc-collector](https://github.com/BCCDC-PHL/routine-sequence-qc-collector), [covid-qc-collector](https://github.com/BCCDC-PHL/covid-qc-collector) 
and [cpo-qc-collector](https://github.com/BCCDC-PHL/cpo-qc-collector) tools, and several others.

# Usage

1. "Import" into a separate GitHub repo
Start by "Importing" this repo on GitHub into a separate repo with a uniqe name (BCCDC-PHL/<YOUR_PROJECT>-qc-collector).
Using the "Import" function as opposed to "forking" the repo allows the new repo to diverge freely from this codebase
without any ongoing connection between them.

2. "Clone" the repo onto your development system
Run:

```
git clone git@github.com:BCCDC-PHL/<YOUR_PROJECT>-qc-collector.git
cd <YOUR_PROJECT>-qc-collector
```

3. Rename the entry point script

Edit the `setup.py` file:

```python
entry_points={
    "console_scripts": [
        "qc-collector = qc_collector.__main__:main",
    ]
},
```


```python
entry_points={
    "console_scripts": [
        "<YOUR_PROJECT>-qc-collector = qc_collector.__main__:main",
    ]
},
```

**Optional**: You may want to rename the `qc_collector` module itself. If you do that, then you'll need to edit any imports or
references in the codebase to match the change.

4. Create and activate a conda environment

Create a conda environment that can be used for development of your tool. You should only need python & pip to get started.

```
conda create -n <YOUR_PROJECT>-qc-collector python=3 pip
```

Activate the conda env:

```
conda activate <YOUR_PROJECT>-qc-collector
```

5. Install this codebase in 'editable' mode.

Run:

```
pip install -e .
```

Now any changes made to the codebase will automatically be reflected in the program when it is run.

6. Prepare a `dev-config.json` file

Copy the `config_template.json` file to create a `dev-config.json`

```
cp config_template.json dev-config.json
```

Edit the `dev-config.json` file to point to the input & output locations you'd like to use while developing your tool.

7. Run the collector

```
<YOUR_PROJECT>-qc-collector --config dev-config.json
```

You should see [JSON Lines-formatted](https://jsonlines.org/) logging output similar to:

```
{"timestamp": "2025-06-02T16:05:20.315", "level": "INFO", "module": "__main__", "function_name": "main", "line_num": 46, "message": {"event_type": "config_loaded", "config_file": "/path/to/dev-config.json"}}
{"timestamp": "2025-06-02T16:05:20.315", "level": "INFO", "module": "core", "function_name": "find_runs", "line_num": 121, "message": {"event_type": "find_runs_start"}}
{"timestamp": "2025-06-02T16:05:20.316", "level": "INFO", "module": "core", "function_name": "find_runs", "line_num": 147, "message": {"event_type": "find_runs_complete"}}
{"timestamp": "2025-06-02T16:05:20.318", "level": "INFO", "module": "__main__", "function_name": "main", "line_num": 62, "message": {"event_type": "write_runs_file_complete", "runs_file": "test_output/sequencing_runs.json"}}
```

The formatting of these log messages is important for compatibility with our [Genomics Services Monitor](https://github.com/BCCDC-PHL/genomics-services-monitor). When adding logging to your project, please ensure that:

1. Each line is a valid JSON-formatted object
2. It includes the keys: `timestamp`, `level`, `module`, `function_name`, `line_num`, `message`
3. The value for the `message` key is a valid JSON-formatted object.

Most of this should be taken care of by the existing logging formatting provided. See other logging statements in this codebase for examples of how to generate logging statements.

8. Edit the codebase to suit the needs of your project.

That's up to you!
