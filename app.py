import streamlit as st
import yaml

st.set_page_config(page_title="Clash 订阅节点精简工具", layout="wide")

st.title("🚀 Clash 订阅一键产品化工具")
st.caption("自动修复空策略组 + 自动处理规则引用强制留存 + 修复指纹警告")

raw_yaml = st.text_area("1. 粘贴订阅内容:", height=300)

if raw_yaml:
    try:
        # 加载配置
        config = yaml.safe_load(raw_yaml)
        
        if 'proxies' not in config:
            st.error("格式错误：未找到 proxies 节点")
        else:
            all_node_names = [p['name'] for p in config['proxies']]
            
            st.write("---")
            keep_names = st.multiselect("2. 选择你要保留的节点:", options=all_node_names)

            if st.button("🛠️ 执行全量修复并生成"):
                if not keep_names:
                    st.warning("请至少选择一个节点")
                else:
                    # --- 阶段 1: 识别“必须保留”的策略组名称 ---
                    required_groups = set()
                    
                    # 从 rules 中提取目标
                    for rule in config.get('rules', []):
                        parts = rule.split(',')
                        if len(parts) >= 3:
                            target = parts[2].strip()
                            if target not in ['DIRECT', 'REJECT', 'ANY']:
                                required_groups.add(target)
                    
                    # 从 rule-providers 中提取目标
                    providers = config.get('rule-providers', {})
                    for p_name in providers:
                        p_target = providers[p_name].get('proxy')
                        if p_target and p_target not in ['DIRECT', 'REJECT']:
                            required_groups.add(p_target)
                    
                    # 默认必留组
                    required_groups.add('主代理') 

                    # --- 阶段 2: 过滤节点实体 ---
                    config['proxies'] = [p for p in config['proxies'] if p['name'] in keep_names]

                    # --- 阶段 3: 递归清理策略组 ---
                    groups = config.get('proxy-groups', [])
                    all_group_names = [g['name'] for g in groups]
                    builtin = ['DIRECT', 'REJECT', 'no-resolve']
                    
                    # 多轮迭代，确保嵌套引用被正确处理
                    for _ in range(5): 
                        valid_targets = set(keep_names + builtin + [g['name'] for g in groups])
                        for g in groups:
                            # 过滤组内成员
                            g['proxies'] = [p for p in g.get('proxies', []) if p in valid_targets]
                            
                            # 核心逻辑：如果组空了但规则需要它，强制塞入 DIRECT 兜底
                            if len(g['proxies']) == 0 and g['name'] in required_groups:
                                g['proxies'] = ['DIRECT']
                        
                        # 仅删除：1.没节点了 2.且规则也没引用它 的组
                        groups = [g for g in groups if len(g['proxies']) > 0 or g['name'] in required_groups]

                    config['proxy-groups'] = groups

                    # --- 阶段 4: 修复 global-client-fingerprint 警告 ---
                    if 'global-client-fingerprint' in config:
                        fp = config.pop('global-client-fingerprint')
                        for p in config['proxies']:
                            if 'client-fingerprint' not in p:
                                p['client-fingerprint'] = fp

                    # --- 阶段 5: 输出 ---
                    final_yaml = yaml.dump(config, allow_unicode=True, sort_keys=False)
                    st.write("---")
                    st.success("✅ 修复完成！所有规则引用均已校对。")
                    st.download_button("💾 点击下载修复后的订阅", final_yaml, "final_config.yaml")
                    st.code(final_yaml, language='yaml')

    except Exception as e:
        st.error(f"解析失败: {str(e)}")
