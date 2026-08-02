"""Existing Study-Hub roles, experts, and deterministic task routing."""

INTERNAL_ROLES = {
    "butler": {"label": "管家", "skill": ".claude/skills/butler/SKILL.md"},
    "product-manager": {"label": "产品经理", "skill": ".agents/skills/product-manager.md"},
    "explorer": {"label": "探索者", "skill": ".agents/skills/explorer.md"},
    "architect": {"label": "架构师", "skill": ".agents/skills/architect.md"},
    "implementer": {"label": "实现者", "skill": ".agents/skills/implementer.md"},
    "auditor": {"label": "审计者", "skill": ".agents/skills/auditor.md"},
    "debugger": {"label": "调试者", "skill": ".agents/skills/debugger.md"},
    "caretaker": {"label": "照料者", "skill": ".agents/skills/caretaker.md"},
    "smoke-tester": {"label": "烟测者", "skill": ".agents/skills/smoke-tester.md"},
}

EXTERNAL_EXPERTS = {
    "automation-expert": {
        "label": "自动化专家",
        "skill": ".agents/skills/automation-expert.md",
        "owner": ".agents/owners/automation-owner.md",
        "keywords": ("视频", "音频", "下载", "解析", "asr", "ffmpeg", "抖音", "b站", "小红书"),
    },
    "frontend-expert": {
        "label": "前端专家",
        "skill": ".agents/skills/frontend-expert.md",
        "owner": ".agents/owners/frontend-owner.md",
        "keywords": ("页面", "按钮", "界面", "显示", "样式", "组件", "表单", "浏览器", "vue"),
    },
    "backend-expert": {
        "label": "后端专家",
        "skill": ".agents/skills/backend-expert.md",
        "owner": ".agents/owners/backend-owner.md",
        "keywords": ("服务", "接口", "api", "数据库", "保存", "路由", "后端"),
    },
    "deploy-expert": {
        "label": "部署专家",
        "skill": ".agents/skills/deploy-expert.md",
        "owner": ".agents/owners/deploy-owner.md",
        "keywords": ("启动", "端口", "部署", "发布", "进程", "环境", "重启"),
    },
    "visual-expert": {
        "label": "视觉专家",
        "skill": ".agents/skills/visual-expert.md",
        "owner": ".agents/owners/visual-owner.md",
        "keywords": ("配色", "字体", "颜色", "图标", "动画", "视觉", "美观", "主题"),
    },
}

TASK_CHAINS = {
    "bug": ("butler", "debugger", "experts", "implementer", "auditor", "smoke-tester"),
    "change": ("butler", "product-manager", "architect", "experts", "implementer", "auditor", "smoke-tester"),
    "research": ("butler", "explorer"),
    "health_check": ("butler", "caretaker", "experts"),
    "deploy": ("butler", "deploy-expert", "smoke-tester"),
    "memory_update": ("butler",),
}


def resolve_experts(description: str) -> tuple[str, ...]:
    """Return every matching expert in stable catalog order."""
    text = (description or "").lower()
    return tuple(
        name
        for name, definition in EXTERNAL_EXPERTS.items()
        if any(keyword.lower() in text for keyword in definition["keywords"])
    )


def recommend_chain(task_type: str) -> tuple[str, ...]:
    """Return the suggested workflow without assigning anyone to the case."""
    return TASK_CHAINS[task_type]
