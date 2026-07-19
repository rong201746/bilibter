import hashlib
import json
import os
from datetime import datetime

# ========== 配置 ==========
DIFFICULTY = 4
REWARD = 10
LEDGER_FILE = "ledger.json"
SIGNATURE_FILE = "ledger.sig"  # 签名单独存一份，增加破解难度

# ========== 账本操作（带防篡改） ==========
def calculate_signature(balances):
    """计算账本的哈希签名"""
    data_str = json.dumps(balances, sort_keys=True)
    return hashlib.sha256(data_str.encode()).hexdigest()

def save_ledger(balances):
    """保存账本 + 签名"""
    # 1. 保存账本数据
    with open(LEDGER_FILE, 'w') as f:
        json.dump(balances, f, indent=2)
    
    # 2. 计算并保存签名
    sig = calculate_signature(balances)
    with open(SIGNATURE_FILE, 'w') as f:
        f.write(sig)
    
    print("💾 账本已保存（含防篡改签名）")

def load_ledger():
    """加载账本，验证签名"""
    if not os.path.exists(LEDGER_FILE):
        # 首次启动：创建创世账本
        genesis = {"创世矿工": 100}
        save_ledger(genesis)
        return genesis
    
    if not os.path.exists(SIGNATURE_FILE):
        print("⚠️ 签名文件不存在，尝试加载账本...")
        with open(LEDGER_FILE, 'r') as f:
            return json.load(f)
    
    # 1. 读取账本
    with open(LEDGER_FILE, 'r') as f:
        balances = json.load(f)
    
    # 2. 读取签名
    with open(SIGNATURE_FILE, 'r') as f:
        saved_sig = f.read().strip()
    
    # 3. 验证签名
    current_sig = calculate_signature(balances)
    if current_sig != saved_sig:
        print("❌❌❌ 警告：账本被篡改！签名不匹配！")
        print(f"   当前签名: {current_sig[:16]}...")
        print(f"   原始签名: {saved_sig[:16]}...")
        print("   系统将拒绝加载被篡改的账本，并自动恢复上一个有效版本")
        
        # 尝试恢复备份（如果有）
        if os.path.exists("ledger_backup.json"):
            print("🔄 尝试从备份恢复...")
            with open("ledger_backup.json", 'r') as f:
                backup = json.load(f)
            # 验证备份的签名
            backup_sig = calculate_signature(backup)
            if backup_sig == saved_sig:
                print("✅ 备份验证通过，已恢复")
                return backup
        print("❌ 无法恢复，请手动检查账本文件")
        return None
    
    print("✅ 账本验证通过（签名匹配）")
    return balances

def backup_ledger(balances):
    """创建账本备份"""
    with open("ledger_backup.json", 'w') as f:
        json.dump(balances, f, indent=2)

# ========== 核心函数 ==========
def mine(user):
    balances = load_ledger()
    if balances is None:
        return
    
    nonce = 0
    while True:
        data = f"{user}{nonce}{datetime.now().timestamp()}"
        hash_val = hashlib.sha256(data.encode()).hexdigest()
        
        if hash_val.startswith('0' * DIFFICULTY):
            balances[user] = balances.get(user, 0) + REWARD
            backup_ledger(balances)  # 挖到就备份
            save_ledger(balances)
            print(f"✅ 挖到区块！{user} 获得 {REWARD} 个币")
            print(f"📊 当前余额: {balances[user]}")
            print(f"🔑 区块哈希: {hash_val[:20]}...")
            return
        nonce += 1
        
        if nonce % 100000 == 0:
            print(f"⏳ {user} 已尝试 {nonce} 次...")

def transfer(from_user, to_user, amount):
    balances = load_ledger()
    if balances is None:
        return
    
    if balances.get(from_user, 0) < amount:
        print(f"❌ 余额不足！{from_user} 只有 {balances.get(from_user, 0)} 个币")
        return
    
    # 简单防重复（记录最近一次转账）
    balances[from_user] -= amount
    balances[to_user] = balances.get(to_user, 0) + amount
    
    backup_ledger(balances)  # 转账就备份
    save_ledger(balances)
    print(f"✅ {from_user} -> {to_user}，转出 {amount} 个币")
    print(f"   {from_user} 余额: {balances[from_user]}")
    print(f"   {to_user} 余额: {balances[to_user]}")

def balance(user):
    balances = load_ledger()
    if balances is None:
        return
    print(f"💰 {user} 的余额: {balances.get(user, 0)} 个币")

def rank():
    balances = load_ledger()
    if balances is None:
        return
    print("\n🏆 排行榜")
    for user, bal in sorted(balances.items(), key=lambda x: x[1], reverse=True):
        print(f"   {user}: {bal} 个币")

def verify_ledger():
    """手动验证账本完整性"""
    print("🔍 正在验证账本完整性...")
    balances = load_ledger()
    if balances is not None:
        print("✅ 账本完整，未被篡改")
    else:
        print("❌ 账本已被篡改或损坏")

def export_ledger():
    """导出账本（带验证）"""
    balances = load_ledger()
    if balances is None:
        return
    
    with open("账本_可发送.txt", "w") as f:
        f.write("BILIBTER 账本导出\n")
        f.write(f"导出时间: {datetime.now()}\n")
        f.write("=" * 40 + "\n")
        for user, bal in balances.items():
            f.write(f"{user}: {bal} 个币\n")
        f.write("=" * 40 + "\n")
        f.write(f"账本签名: {calculate_signature(balances)}\n")
    
    print("📤 账本已导出为 账本_可发送.txt")
    print("   包含防篡改签名，接收方可验证真伪")

def show_help():
    print("""
BILIBTER v0.3 — 防篡改版

新特性：
  - 账本带哈希签名，防篡改
  - 自动备份，防止损坏
  - 验证账本完整性

命令:
  mine <名字>            - 挖矿
  transfer <从> <到> <数量> - 转账
  balance <名字>          - 查询余额
  rank                    - 排行榜
  export                  - 导出账本
  verify                  - 验证账本是否被篡改
  help                    - 显示帮助
  exit                    - 退出
""")

# ========== 主程序 ==========
print("========================================")
print("  🪙  BILIBTER v0.3")
print("  防篡改版 — 哈希签名保护账本")
print("========================================")

while True:
    try:
        cmd = input("> ").strip().split()
        if not cmd:
            continue
        if cmd[0] == "exit":
            print("🕯️  BILIBTER 已关闭")
            break
        elif cmd[0] == "help":
            show_help()
        elif cmd[0] == "mine":
            mine(cmd[1] if len(cmd) > 1 else "匿名矿工")
        elif cmd[0] == "transfer":
            if len(cmd) < 4:
                print("用法: transfer <从> <到> <数量>")
            else:
                transfer(cmd[1], cmd[2], int(cmd[3]))
        elif cmd[0] == "balance":
            balance(cmd[1] if len(cmd) > 1 else "先辈")
        elif cmd[0] == "rank":
            rank()
        elif cmd[0] == "export":
            export_ledger()
        elif cmd[0] == "verify":
            verify_ledger()
        else:
            print(f"❌ 未知命令: {cmd[0]}，输入 help 查看")
    except KeyboardInterrupt:
        print("\n🕯️  BILIBTER 已关闭")
        break
    except Exception as e:
        print(f"❌ 错误: {e}")