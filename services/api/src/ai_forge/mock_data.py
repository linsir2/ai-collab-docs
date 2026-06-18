TECH_REVIEWER_FORGES = [
    {
        "role": "TechReviewer",
        "type": "doc_ai",
        "airity": "doc_ai:TechReviewer",
        "proposals": [
            {
                "instruction_hint": "安全|加密|权限",
                "old_hint": "加密传输",
                "new_text": "所有数据传输采用TLS 1.3协议加密，并对静态数据实施AES-256加密存储，密钥通过KMS进行轮换管理。系统需通过等保三级认证安全基线。",
                "rationale": "当前版本仅提及加密传输，缺少静态加密和密钥管理描述，不符合ISO 27001对数据保护的要求。",
                "diff_summary": "+45/-12行，补充安全架构细节",
            },
            {
                "instruction_hint": "数据库|存储|持久化",
                "old_hint": "使用数据库",
                "new_text": "采用PostgreSQL 15主从架构，主库负责写入，只读副本承担报表查询负载。配置WAL日志持续归档到S3兼容存储，RPO<5分钟。",
                "rationale": "数据库方案描述过于简略，需明确技术选型和高可用策略。",
                "diff_summary": "+28/-5行，补充数据库架构细节",
            },
            {
                "instruction_hint": "架构|系统|部署",
                "old_hint": "部署到服务器",
                "new_text": "基于Kubernetes 1.29部署，服务以Deployment方式运行3副本，配置HPA基于CPU/内存自动扩缩。Ingress通过Nginx Controller统一流量接入，服务间通信走Service Mesh Istio。",
                "rationale": "部署方案需具体化技术栈，体现企业级运维能力。",
                "diff_summary": "+52/-8行，补充部署架构",
            },
        ],
    },
]

LEGAL_AGENT_FORGES = [
    {
        "role": "LegalAgent",
        "type": "doc_ai",
        "airity": "doc_ai:LegalAgent",
        "proposals": [
            {
                "instruction_hint": "合规|法务|合同",
                "old_hint": "合同审查",
                "new_text": "系统内置合同条款合规检查引擎，覆盖《民法典》合同编核心条款。自动化审查规则基于中国法律数据库v2024，并支持法务团队自定义合规规则集。",
                "rationale": "法律依据需明确引用，增强文档权威性和可信度。",
                "diff_summary": "+38/-10行，补充合规依据",
            },
            {
                "instruction_hint": "数据|隐私|GDPR",
                "old_hint": "用户数据",
                "new_text": "用户个人信息处理严格遵循《个人信息保护法》，数据收集遵循最小必要原则。提供用户数据导出与删除功能，注销后30天内完成数据清理。跨境数据传输需用户明示同意。",
                "rationale": "隐私保护条款缺少具体执行标准，需引用明确法律条文。",
                "diff_summary": "+42/-15行，补充隐私条款",
            },
            {
                "instruction_hint": "安全|架构|技术",
                "old_hint": "安全架构",
                "new_text": "本项目聚焦于法务合规领域，建议精简纯技术架构描述，保留与合规直接相关的安全要素。非必要的技术细节（如K8s版本号、HPA参数）可移至附录。",
                "rationale": "过多技术细节会分散读者对合规核心内容的注意力，降低文档可读性。",
                "diff_summary": "-35/+5行，建议精简技术描述",
            },
        ],
    },
]

PERSONAL_AI_FORGES = [
    {
        "role": "我的技术顾问",
        "type": "personal_ai",
        "airity": "personal_ai",
        "proposals": [
            {
                "instruction_hint": "技术|方案|设计",
                "old_hint": "技术方案",
                "new_text": "建议在架构设计中引入事件驱动模式，使用消息队列解耦核心服务。微服务间通过异步事件通信，提高系统韧性和可扩展性。",
                "rationale": "基于你对高扩展性系统的偏好，事件驱动架构更符合你的技术理念。",
                "diff_summary": "+32/-8行，引入事件驱动",
            },
            {
                "instruction_hint": "性能|优化|速度",
                "old_hint": "性能优化",
                "new_text": "建议在数据查询层引入Redis缓存热点数据，对高频查询接口实施多级缓存策略（本地Caffeine + 分布式Redis），预期P99延迟降低60%以上。",
                "rationale": "你一直关注系统性能，缓存策略是比较成熟的优化路径。",
                "diff_summary": "+25/-5行，补充缓存策略",
            },
        ],
    },
    {
        "role": "我的文案助手",
        "type": "personal_ai",
        "airity": "personal_ai",
        "proposals": [
            {
                "instruction_hint": "表述|文案|优化",
                "old_hint": "优化表述",
                "new_text": "「系统具备高可用性」改为「系统全年可用性达99.95%，计划内停机窗口每年不超过4小时」。使用量化数据替代模糊表述，增强可信度。",
                "rationale": "量化表述比形容词更有说服力，符合严谨技术文档风格。",
                "diff_summary": "+12/-6行，量化表述",
            },
            {
                "instruction_hint": "结构|组织|大纲",
                "old_hint": "调整结构",
                "new_text": "建议将「安全保障」章节提前到「架构设计」之后，放在「部署方案」之前。这样符合技术方案文档的标准阅读顺序：需求→架构→安全→部署→运维。",
                "rationale": "调整章节顺序可以让文档逻辑更顺畅，先解决安全问题再谈部署。",
                "diff_summary": "结构调整建议，不变更内容",
            },
        ],
    },
]

CONFLICT_PAIRS = [
    {
        "block_hint": "安全架构描述",
        "proposal_a": {
            "ai_source": "doc_ai:TechReviewer",
            "role": "TechReviewer",
            "new_content": "系统安全架构采用纵深防御模型，包含网络隔离（VPC+安全组）、应用安全（WAF+RASP）、数据安全（加密+脱敏）三层防护。所有对外接口实施OAuth 2.0认证，审计日志实时写入不可变存储。",
            "rationale": "安全架构描述过于简略，需补充纵深防御的完整层次，这是等保认证的技术要求。",
            "diff_summary": "+48/-10行，扩充安全架构",
        },
        "proposal_b": {
            "ai_source": "doc_ai:LegalAgent",
            "role": "LegalAgent",
            "new_content": "系统安全措施满足《网络安全法》和等保二级基本要求，具体技术实施方案请参见附录。正文聚焦于合规审查功能的业务描述，避免过多技术实现细节。",
            "rationale": "此文档面向法务团队，过多技术细节会降低可读性。安全技术细节应放在附录供技术人员参考。",
            "diff_summary": "-28/+5行，精简技术细节移至附录",
        },
        "conflict_reason": "TechReviewer要求扩充安全架构细节，LegalAgent主张精简技术内容保持可读性——两者对文档详略方向完全对立。",
    }
]
