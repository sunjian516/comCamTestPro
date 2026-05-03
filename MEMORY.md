重启gateway前：killall相关进程 → rm -f ~/.hermes/*.pid → 再启动
§
知识库路径：E:\her\workspace\02 知识库\
三个知识库分类：
1. 项目管理（采购计划）：2026年系统所辖采购计划表.pdf - 2026年采购项目清单，含预算、负责人、招标方式
2. 现场设备管理（设备台账）：设备台账.xls - 27959行，虹桥机场设备台账，含设备编号/名称/位置/状态/保管人等
3. 系统管理（运维手册）：附件一：机电信息保障部运行维护手册-系统运行部.pdf - 1045页，覆盖离港/集成/航显/广播/监控/网络等20+系统运维手册
**T2泊位系统（ADB Safegate Safedock A-VDGS）运维手册：03 T2泊位系统运维手册/**
  - 显示单元UM-4050（36页）：飞行员显示屏，安装维护指南
  - 操作面板UM-4046_FOP2（44页）：第二代固定式手动操作面板，安装维护
  - 扫描单元UM-4008（224页）：Safedock X A-VDGS核心扫描单元，最详细
§
临时文件工作目录：E:\her\workspace\00 临时文件\（通过/mnt/e/her/workspace/00 临时文件访问）。需要临时存放文件时使用此目录，不要放Windows桌面。
§
合同文件路径：E:\her\workspace\02 知识库\01 系统合同\（01建设合同2556文件，02运维合同453文件，共3009个，主合同867个PDF/DOCX/DOC）
OCR方案：Tesseract 4.1.1（/home/dministrator/tesseract_full/extracted/）+ PyMuPDF渲染PDF页面 + chi_sim语言包在/tmp/tessdata/。WSL无root无法apt-get，用dpkg-deb手动下载解压+依赖链方式安装。
原始Excel数据（运保合同全生命周期管理表_更新.xlsx）有批量错误：14个合同金额小数点错位100倍，需修正。
§
GitHub仓库: https://github.com/sunjian516/comCamTestPro（用于推送自主开发项目）
§
代码开发遵循 Andrej Karpathy 四条黄金法则（来源：~/.hermes/prompts/karpathy_rules.md）：1）先思考再行动——不明确的需求必须追问，呈现多种方案；2）简洁优先——不加未被要求的功能，不为一次性代码建抽象；3）外科手术式修改——只改必要的代码，不重构没坏的东西；4）目标驱动执行——所有任务转化为可验证目标，先写测试再实现。执行流程：分析需求→提出方案→确认方案→简洁实现→验证测试。
§
系统运行部周报/月报分析流程：
- 每周一/二收到汇总Word周报后，按固定模板分析：工作量排行、亮点工作、风险提示、工作量对比
- 每月1号自动汇总前一个月4次周报，形成科室月度分析报告，供绩效考核参考
- 分析维度：任务数量、跨部门协作、项目推进、安全风险、工作亮点
§
Cron任务推送偏好：cron job的执行状态日志（如"Cronjob Response: ..."）不需要推送，只保留结果在本地。需要推送的是实际内容（如会议提醒、绩效分析报告）。设置方法：deliver改为"local"。
§
GitHub备份规范（仓库：sunjian516/comCamTestPro）：
- 目录结构：根目录直接放 MEMORY.md、USER.md、SOUL.md、jobs.json、skills/*.md
- 每次备份更新README.md的记录表格
- 私密数据（meetings_latest.txt、meeting_reminders_log.txt）永不上传
- 不保留旧tar.gz压缩包，只备份配置文件
§
Wiki已初始化于 ~/wiki（/home/dministrator/wiki/），共45个页面，涵盖泊位系统手册、1045页运维手册（27系统）、设备台账摘要、采购计划。用户主动要求我自主建立定期维护任务（月度lint），说明信任我的主动性。
§
运保合同表（运保合同全生命周期管理表.xlsx）用户明确要求不摄入wiki。
§
用户正在系统性地一个一个学习技能，一个接一个。
§
用户说"按照你的节奏开始吧"时表示信任我的执行节奏，会让我自己推进。
§
邮件技能（himalaya）用户暂不配置，未来可能启用。
§
新项目：USB摄像头RTSP流 → 实时识别孙剑 → 微信通知
- RTSP地址: rtsp://10.104.0.170:8554/live
- RTSP认证: admin / sunjian123
- Windows侧IP摄像头软件（有认证）
- WSL USB passthrough对该摄像头支持不完整（uvcvideo初始化失败）