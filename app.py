import os
import json
import uuid
import asyncio
import random
from datetime import datetime
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# OpenAI API設定
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
