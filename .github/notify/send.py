#!/usr/bin/env python3
"""渲染自定义邮件模板，并通过 SMTP 发送流水线结果通知

用途：替代 GitHub 自带的失败通知邮件（自带邮件内容固定、无法加部署成功通知），由
.github/workflows/notify.yml 统一调用，模板在 .github/notify/templates/ 下按状态各一份

环境变量：
  MAIL_SERVER / MAIL_PORT / MAIL_FROM / MAIL_TO   仓库 Variable，端口 465 走 SSL，其它端口走 STARTTLS
  MAIL_USERNAME / MAIL_PASSWORD                   仓库 Secret，MAIL_PASSWORD 为 SMTP 授权码（不是登录密码）
  NOTIFY_*                                        由 notify.yml 从调用方输入透传
  GITHUB_* / COMMIT_MSG                           运行时上下文，由 Actions 注入或工作流传入

未配置 MAIL_SERVER 或 MAIL_TO 时只打印 notice 后退出 0，不阻断流水线
"""

import html
import os
import re
import smtplib
import ssl
import sys
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

# 状态 → (中文标签, 主题色)，与模板里的 {{STATUS_LABEL}} / {{STATUS_COLOR}} 对应
STATUS_META = {
    "success": ("成功", "#1f883d"),
    "failure": ("失败", "#cf222e"),
    "cancelled": ("已取消", "#9a6700"),
}

# 邮件内时间统一按北京时间展示，runner 默认是 UTC
LOCAL_TZ = timezone(timedelta(hours=8))

# 提交说明在邮件里只展示首行且限长，避免合并提交的多段正文撑爆表格
COMMIT_MSG_LIMIT = 100


def env(name: str, default: str = "") -> str:
    """读取环境变量并去掉首尾空白，空值回落到默认值"""
    return (os.environ.get(name) or "").strip() or default


def esc(value: str) -> str:
    """HTML 转义，提交说明与分支名可能带尖括号或引号"""
    return html.escape(value, quote=True)


def ann(level: str, message: str) -> None:
    """输出 GitHub 注解，多行内容按工作流命令规范转义换行"""
    text = message.replace("%", "%25").replace("\r", "").replace("\n", "%0A")
    print(f"::{level}::{text}")


def split_list(value: str) -> list:
    """拆分收件人：优先按逗号/分号，剩一个不带显示名的整体时再按空白拆"""
    items = [item.strip() for item in re.split(r"[,;]+", value) if item.strip()]
    if len(items) == 1 and " " in items[0] and "<" not in items[0]:
        items = items[0].split()
    return items


def parse_port(value: str) -> int:
    """端口解析失败时回落到 465，避免一个笔误让整封通知丢掉"""
    try:
        return int(value) if value else 465
    except ValueError:
        ann("warning", f"MAIL_PORT 不是数字（{value}），按 465 处理")
        return 465


def parse_secure(value: str, port: int) -> bool:
    """MAIL_SECURE 优先，未配置时 465 按隐式 SSL，与 NestJS 侧 nodemailer 的 secure 语义一致"""
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes"):
        return True
    if normalized in ("false", "0", "no"):
        return False
    return port == 465


def build_rows(details: str, base_rows: list) -> str:
    """把「键=值」明细与基础上下文行渲染成表格，调用方明细在前"""
    pairs = []
    for line in details.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        pairs.append((key.strip(), value.strip()))
    pairs.extend(base_rows)
    rows = []
    for key, value in pairs:
        if not key:
            continue
        rows.append(
            "<tr>"
            f'<td style="padding:7px 0;width:96px;white-space:nowrap;vertical-align:top;color:#656d76;">{esc(key)}</td>'
            f'<td style="padding:7px 0;vertical-align:top;word-break:break-all;">{esc(value) or "-"}</td>'
            "</tr>"
        )
    return "".join(rows)


def build_note(note: str) -> str:
    """附加提示块，未提供时不渲染这一行"""
    if not note:
        return ""
    body = "<br />".join(esc(line) for line in note.splitlines() if line.strip())
    return (
        "<tr><td style=\"padding:0 24px 18px;\">"
        '<div style="padding:12px 14px;background:#fff8c5;border:1px solid #d4a72c66;'
        'border-radius:8px;font-size:13px;line-height:1.7;color:#57606a;">'
        f"{body}</div></td></tr>"
    )


def render(template: str, values: dict) -> str:
    """按 {{KEY}} 占位符替换，未提供的占位符原样保留便于发现模板笔误"""
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def send_mail(cfg: dict, subject: str, plain: str, body: str) -> None:
    """按 secure 选择隐式 SSL 或 STARTTLS，发送 multipart/alternative 邮件"""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((cfg["from_name"], cfg["from_addr"])) if cfg["from_name"] else cfg["from_addr"]
    message["To"] = ", ".join(cfg["to"])
    message.set_content(plain)
    message.add_alternative(body, subtype="html")

    context = ssl.create_default_context()
    if cfg["secure"]:
        client = smtplib.SMTP_SSL(cfg["server"], cfg["port"], context=context, timeout=30)
    else:
        client = smtplib.SMTP(cfg["server"], cfg["port"], timeout=30)
        client.starttls(context=context)
    try:
        if cfg["username"] and cfg["password"]:
            client.login(cfg["username"], cfg["password"])
        client.send_message(message)
    finally:
        client.quit()


def main() -> int:
    """组装上下文、渲染模板并发送，任何非致命问题都以 notice / warning 呈现"""
    # 变量名与 NestJS 侧 application.yaml 的 mail.* 对齐，MAIL_SERVER 仅为历史兼容
    server = env("MAIL_HOST") or env("MAIL_SERVER")
    recipients = split_list(env("MAIL_TO"))
    if not server or not recipients:
        ann("notice", "未配置 MAIL_HOST / MAIL_TO，跳过邮件通知（在仓库 Settings → Secrets and variables → Actions 补齐）")
        return 0

    username = env("MAIL_USERNAME")
    password = env("MAIL_PASSWORD")
    from_addr = env("MAIL_FROM", username)
    if not from_addr:
        ann("warning", "缺少 MAIL_FROM 且未配置 MAIL_USERNAME，无法确定发件人，跳过邮件通知")
        return 0
    if not username or not password:
        ann("warning", "缺少 Secret MAIL_USERNAME / MAIL_PASSWORD（SMTP 授权码），跳过邮件通知")
        return 0

    status = env("NOTIFY_STATUS", "failure").lower()
    label, color = STATUS_META.get(status, STATUS_META["failure"])
    title = env("NOTIFY_TITLE", "流水线通知")
    summary = env("NOTIFY_SUMMARY") or f"{title} 结果为{label}"

    # 允许调用方指定模板名；默认成功走 success.html，失败与取消共用 failure.html
    template_name = env("NOTIFY_TEMPLATE") or ("success" if status == "success" else "failure")
    template_path = TEMPLATE_DIR / f"{template_name}.html"
    if not template_path.is_file():
        ann("warning", f"邮件模板不存在: {template_path}，跳过邮件通知")
        return 0

    github_server = env("GITHUB_SERVER_URL", "https://github.com")
    repo = env("GITHUB_REPOSITORY", "-")
    sha = env("GITHUB_SHA")
    sha_short = sha[:7] if sha else "-"
    run_id = env("GITHUB_RUN_ID")
    run_number = env("GITHUB_RUN_NUMBER", "-")
    run_url = f"{github_server}/{repo}/actions/runs/{run_id}" if run_id else f"{github_server}/{repo}/actions"

    base_rows = [("仓库", repo), ("分支/标签", env("GITHUB_REF_NAME", "-"))]
    commit_msg = env("COMMIT_MSG").splitlines()[0].strip() if env("COMMIT_MSG") else ""
    if commit_msg:
        base_rows.append(("提交说明", commit_msg[:COMMIT_MSG_LIMIT]))
    base_rows.extend(
        [
            ("提交", sha_short),
            ("触发人", env("GITHUB_ACTOR", "-")),
            ("触发事件", env("GITHUB_EVENT_NAME", "-")),
            ("运行编号", f"#{run_number}"),
        ]
    )

    values = {
        "TITLE": esc(title),
        "STATUS_LABEL": label,
        "STATUS_COLOR": color,
        "SUMMARY": "<br />".join(esc(line) for line in summary.splitlines() if line.strip()),
        "DETAIL_ROWS": build_rows(env("NOTIFY_DETAILS"), base_rows),
        "NOTE_BLOCK": build_note(env("NOTIFY_NOTE")),
        "RUN_URL": esc(run_url),
        "RUN_TEXT": f"查看运行 #{run_number}",
        "TIMESTAMP": datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S"),
        "FOOTER": "本邮件由 GitHub Actions 自动发送，收件人由仓库 Variable MAIL_TO 指定",
    }

    body = render(template_path.read_text(encoding="utf-8"), values)
    subject = f"【{label}】{title} · {repo} · {env('GITHUB_REF_NAME', '-')} @ {sha_short}"

    plain_lines = [f"【{label}】{title}", "", summary, ""]
    for line in env("NOTIFY_DETAILS").splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            plain_lines.append(f"{key.strip()}: {value.strip()}")
    if commit_msg:
        plain_lines.append(f"提交说明: {commit_msg[:COMMIT_MSG_LIMIT]}")
    plain_lines.extend(
        [
            f"仓库: {repo}",
            f"分支/标签: {env('GITHUB_REF_NAME', '-')}",
            f"提交: {sha_short}",
            f"运行: {run_url}",
        ]
    )
    note = env("NOTIFY_NOTE")
    if note:
        plain_lines.extend(["", note])
    plain = "\n".join(plain_lines)

    port = parse_port(env("MAIL_PORT"))
    cfg = {
        "server": server,
        "port": port,
        "secure": parse_secure(env("MAIL_SECURE"), port),
        "from_addr": from_addr,
        "from_name": env("MAIL_FROM_NAME", "mix-web-demo CI"),
        "to": recipients,
        "username": username,
        "password": password,
    }

    try:
        send_mail(cfg, subject, plain, body)
    except Exception as exc:  # noqa: BLE001 - 通知失败原因需原样暴露给运维
        ann("error", f"邮件发送失败: {type(exc).__name__}: {exc}")
        return 1

    ann("notice", f"邮件已发送: {subject} → {len(recipients)} 个收件人（模板 {template_name}.html）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
