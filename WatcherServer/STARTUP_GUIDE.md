[English](STARTUP_GUIDE.md) | [中文](STARTUP_GUIDE_CN.md)

# Quick Start Script Usage

## Windows Users

Simply double-click the `start.bat` file to start the service.

Or run in command line:
```cmd
start.bat
```

## Linux/Mac Users

After granting execute permissions, run:
```bash
chmod +x start.sh
./start.sh
```

## Script Features

The startup script automatically performs the following steps:

1. **Check conda environment**: Ensure conda is installed
2. **Activate environment**: Activate the `watcher-server` conda environment
3. **Check configuration**: If `.env` doesn't exist, automatically copy from `.env.example`
4. **Start service**: Run `python src/main.py`

## First Run

If running for the first time, please create the conda environment first:

```bash
# Windows/Linux/Mac
conda env create -f environment.yml
```

Then run the startup script.
