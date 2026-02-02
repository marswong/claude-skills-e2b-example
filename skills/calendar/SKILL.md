---
name: calendar
description: Manage Google Calendar events including viewing, creating, quick-adding with natural language, and setting reminders. Use when user wants to check schedule, create meetings, add events, or set reminders.
---

# Calendar 日历管理 Skill

Google 日历集成，支持日程的增删改查、自然语言添加、提醒设置等。

## 快速开始

### 1. 安装依赖

```bash
pip3 install google-auth-oauthlib google-api-python-client
```

### 2. 配置 Google 凭据

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 **Google Calendar API**
4. 创建 **OAuth 2.0 凭据** (选择"桌面应用")
5. 下载 JSON 文件并保存到 `~/.claude/credentials/google_credentials.json`

### 3. 首次授权

```bash
python3 ~/.claude/skills/calendar/scripts/calendar_module.py setup
```

会打开浏览器进行 Google 账户授权。

## 功能列表

### 1. 查看日程

```bash
# 查看未来事件 (默认10个)
python3 ~/.claude/skills/calendar/scripts/calendar_module.py list

# 查看今日日程
python3 ~/.claude/skills/calendar/scripts/calendar_module.py list --today

# 查看本周日程
python3 ~/.claude/skills/calendar/scripts/calendar_module.py list --week

# 限制数量
python3 ~/.claude/skills/calendar/scripts/calendar_module.py list -n 5
```

### 2. 创建事件

```bash
# 基本创建
python3 ~/.claude/skills/calendar/scripts/calendar_module.py create "团队会议" --start "2026-01-20 10:00"

# 指定时长 (分钟)
python3 ~/.claude/skills/calendar/scripts/calendar_module.py create "午餐" --start "2026-01-20 12:00" --duration 90

# 添加地点和描述
python3 ~/.claude/skills/calendar/scripts/calendar_module.py create "客户会议" \
  --start "2026-01-20 14:00" \
  --location "会议室A" \
  --description "讨论Q1计划"

# 邀请参与者
python3 ~/.claude/skills/calendar/scripts/calendar_module.py create "项目评审" \
  --start "2026-01-20 15:00" \
  --attendees user1@example.com user2@example.com
```

### 3. 快速添加 (自然语言)

```bash
python3 ~/.claude/skills/calendar/scripts/calendar_module.py quick "Meeting tomorrow at 3pm"
python3 ~/.claude/skills/calendar/scripts/calendar_module.py quick "Lunch with John tomorrow at noon"
python3 ~/.claude/skills/calendar/scripts/calendar_module.py quick "Dentist appointment Jan 25 10am"
```

### 4. 创建提醒

```bash
python3 ~/.claude/skills/calendar/scripts/calendar_module.py remind "给妈妈打电话" --time "2026-01-20 18:00"
python3 ~/.claude/skills/calendar/scripts/calendar_module.py remind "提交报告" --time "2026-01-21 09:00"
```

### 5. 删除事件

```bash
python3 ~/.claude/skills/calendar/scripts/calendar_module.py delete <event_id>
```

### 6. 查看日历列表

```bash
python3 ~/.claude/skills/calendar/scripts/calendar_module.py calendars
```

## Python 模块使用

```python
from calendar_module import CalendarClient

client = CalendarClient()

# 查看未来事件
events = client.list_events(max_results=10)
for event in events['events']:
    print(f"{event['start']}: {event['summary']}")

# 创建事件
result = client.create_event(
    summary="团队会议",
    start="2026-01-20 10:00",
    duration=60,
    location="会议室A",
    description="讨论Q1计划",
    attendees=["user@example.com"]
)
print(f"事件已创建: {result['event']['link']}")

# 快速添加
result = client.quick_add("Meeting tomorrow at 3pm")
print(f"事件已创建: {result['event']['summary']}")

# 创建提醒
result = client.create_reminder(
    title="给妈妈打电话",
    time="2026-01-20 18:00"
)

# 查看今日日程
today_events = client.get_today_events()

# 查看本周日程
week_events = client.get_week_events()

# 检查可用性
availability = client.check_availability(
    start="2026-01-20 10:00",
    end="2026-01-20 11:00"
)
print(f"时段可用: {availability['available']}")

# 删除事件
client.delete_event(event_id="xxx")
```

## 参数说明

### 创建事件

| 参数 | 说明 |
|------|------|
| `--start` | 开始时间 (YYYY-MM-DD HH:MM) |
| `--end` | 结束时间 |
| `--duration` | 时长 (分钟)，默认 60 |
| `--location` | 地点 |
| `--description` | 描述 |
| `--attendees` | 参与者邮箱列表 |

### 查看事件

| 参数 | 说明 |
|------|------|
| `-n` / `--max` | 最大数量 |
| `--today` | 仅今日 |
| `--week` | 本周 |

## 时间格式

支持的时间格式：
- `2026-01-20 10:00`
- `2026-01-20 10:00:00`
- `2026-01-20T10:00:00`
- `2026-01-20`
- `01/20/2026 10:00`

## 凭据文件位置

- Google 凭据: `~/.claude/credentials/google_credentials.json`
- 授权 Token: `~/.claude/credentials/google_calendar_token.json` (自动生成)

## 常见问题

### 授权失败

1. 确保已在 Google Cloud Console 启用 Calendar API
2. 检查 OAuth 凭据类型是否为"桌面应用"
3. 删除 `~/.claude/credentials/google_calendar_token.json` 后重新运行 setup

### 时区问题

默认使用系统时区，支持：
- CST (中国标准时间)
- PST (太平洋时间)
- EST (东部时间)
- UTC

---

**费用**: 免费
**服务**: Google Calendar API
**依赖**: google-auth-oauthlib, google-api-python-client
