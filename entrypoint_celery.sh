#!/bin/bash

# Downloads the tools
python superagi/tool_manager.py
python -m pip install flower
# Install dependencies
./install_tool_dependencies.sh

exec celery -A superagi.worker worker --beat --loglevel=info & celery -A superagi.worker flower