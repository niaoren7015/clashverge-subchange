import streamlit as st
import yaml

st.set_page_config(page_title="Clash 订阅完美精简工具", layout="wide")

st.title("🛠️ Clash 订阅自动修复工具")
st.caption("解决空策略组导致的 'missing proxies' 校验错误")

raw_yaml = st.text_area("1. 粘贴订阅内容:", height=300)

if raw_yaml:
    try:
        # 使用 safe_load 保持结构
        config = yaml.safe_load(raw_yaml)
        
        if 'proxies' not in config:
            st.error("格式错误：未找到 proxies 节点")
        else:
            all_nodes = [p['name'] for p in config['proxies']]
            
            st.write("---")
            keep_names = st.multiselect("2. 选择要保留的节点:", options=all_nodes)

            if st.button("🚀 生成可用配置") and keep_names:
                # A. 仅保留选中的节点实体
                config['proxies'] = [p for p in config['proxies'] if p['name'] in keep_names]
                
                # B. 递归清理策略组
                def clean_groups(config, keep_names):
                    groups = config.get('proxy-groups', [])
                    builtin = ['DIRECT', 'REJECT', 'no-resolve']
                    
                    # 记录当前有效的“目标”（节点名 + 内置名）
                    valid_targets = set(keep_names + builtin)
                    
                    # 循环多次直到没有组再被剔除（处理嵌套引用）
                    for _ in range(len(groups)):
                        active_group_names = []
                        for g in groups:
                            # 过滤该组内的成员：必须在有效目标里，或者是一个非空的组名
                            original_proxies = g.get('proxies', [])
                            g['proxies'] = [p for p in original_proxies if p in valid_targets]
                            
                            # 如果该组过滤后不为空，则该组名也是“有效目标”
                            if len(g['proxies']) > 0:
                                active_group_names.append(g['name'])
                        
                        new_valid_targets = set(keep_names + builtin + active_group_names)
                        if new_valid_targets == valid_targets:
                            break
                        valid_targets = new_valid_targets
                    
                    # 最后只保留非空的策略组
                    config['proxy-groups'] = [g for g in groups if len(g.get('proxies', [])) > 0]

                clean_groups(config, keep_names)

                # C. 处理 deprecated 警告 (顺手修复你截图中的 warning)
                if 'global-client-fingerprint' in config:
                    fp = config.pop('global-client-fingerprint')
                    for p in config['proxies']:
                        if 'client-fingerprint' not in p:
                            p['client-fingerprint'] = fp

                # 输出
                result = yaml.dump(config, allow_unicode=True, sort_keys=False)
                st.write("---")
                st.success("配置已修复！已自动剔除所有空策略组。")
                st.download_button("💾 下载可用订阅文件", result, "fixed_config.yaml")
                st.code(result, language='yaml')

    except Exception as e:
        st.error(f"解析失败: {str(e)}")
