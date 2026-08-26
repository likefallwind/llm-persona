1. 本仓库的目标是想要研究不同大模型的性格，希望最终能够达到一篇有分量的顶会论文要求
2. /home/likefallwind/code/edubenchmark  这个目录下，有大量不同模型的评测，尤其是minimax m3, minimax m2.7, glm5.2 doubao-2.0-pro doubao-2.0-lite deepseek-v4-pro qwen3.5-4b 6个模型都有全量的回复，他们回复基于的问题、harness都完全一样，且数据是海量的
3. 这个研究我建议完全靠agent，不要做任何人类标注；如果觉得现在不够，可以调用这些模型补充实验
4. 具体api在环境变量里面，其中minimax m3, minimax m2.7使用minimax官方，注意最大并发不要超过4；glm5.2, doubao-2.0-lite, deepseek-v4-pro请使用api gateway，最大并发不要超过8（doubao-2.0-pro目前已经无法使用了，变成doubao-2.1-turbo了），qwen3.5-4b如果要使用你把需求记下来，后续我需要单独配置；这些使用方式，都可以参考 edubenchmark里面的调用方法
5. 最终结论一定要经得起推敲，并且相比于已有研究，有足够创新
