#!/usr/bin/env python3
"""
Calendar Skills 测试页面 - Flask 后端
"""

import sys
import os

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from flask import Flask, request, jsonify, send_file
from calendar_module import CalendarClient

app = Flask(__name__)
client = None

def get_client():
    global client
    if client is None:
        client = CalendarClient()
    return client

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/events', methods=['GET'])
def list_events():
    """获取日历事件"""
    try:
        view = request.args.get('view', 'upcoming')
        c = get_client()

        if view == 'today':
            result = c.get_today_events()
        elif view == 'week':
            result = c.get_week_events()
        else:
            result = c.list_events(max_results=20)

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events', methods=['POST'])
def create_event():
    """创建事件"""
    try:
        data = request.json
        c = get_client()

        if data.get('quick'):
            # 自然语言快速创建
            result = c.quick_add(data['quick'])
        else:
            # 标准创建
            result = c.create_event(
                summary=data.get('summary', 'New Event'),
                start=data.get('start'),
                end=data.get('end'),
                duration=data.get('duration', 60),
                location=data.get('location'),
                description=data.get('description')
            )

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    """删除事件"""
    try:
        c = get_client()
        result = c.delete_event(event_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/remind', methods=['POST'])
def create_reminder():
    """创建提醒"""
    try:
        data = request.json
        c = get_client()
        result = c.create_reminder(
            title=data.get('title'),
            time=data.get('time')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/calendars', methods=['GET'])
def list_calendars():
    """获取日历列表"""
    try:
        c = get_client()
        result = c.list_calendars()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Calendar Skills 测试页面")
    print("  访问: http://localhost:8080")
    print("="*50 + "\n")
    app.run(debug=True, port=8080)
